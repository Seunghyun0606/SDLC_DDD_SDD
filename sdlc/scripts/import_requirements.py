#!/usr/bin/env python3
"""Bulk requirement intake PoC for the AI-SDLC Harness (stdlib only).

Reads a two-row-header XLSX requirement list and emits a provenance-preserving
candidate model. It never silently merges similar requirement groups.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL = "http://schemas.openxmlformats.org/package/2006/relationships"

DEFAULT_MAPPING = {
    "No": "source_sequence",
    "Level1": "level1",
    "Level2": "level2",
    "요구사항 ID": "external_requirement_id",
    "요구사항명": "source_requirement_name",
    "요구사항": "source_requirement_text",
    "시작일": "planned_start",
    "종료일": "planned_end",
    "담당자": "assignee",
}
REQUIRED = {"level1", "level2", "external_requirement_id", "source_requirement_name", "source_requirement_text"}


@dataclass
class IntakeProfile:
    effective_header_row: int = 2
    preserve_group_header_row: bool = True
    mapping: dict[str, str] | None = None

    def __post_init__(self):
        if self.mapping is None:
            self.mapping = dict(DEFAULT_MAPPING)


def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.lower() in {"true", "false"}:
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        return v


def load_profile(path: Path | None) -> IntakeProfile:
    if path is None:
        return IntakeProfile()
    lines = path.read_text(encoding="utf-8").splitlines()
    effective = 2
    preserve_group_header_row = True
    mapping: dict[str, str] = {}
    current: dict[str, str] | None = None
    in_mapping = False
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("effective_row:"):
            effective = int(_scalar(s.split(":", 1)[1]))
        if s.startswith("preserve_group_header_row:"):
            preserve_group_header_row = bool(_scalar(s.split(":", 1)[1]))
        if s == "mapping:":
            in_mapping = True
            continue
        if in_mapping and raw.startswith("  - "):
            if current and "source_label" in current and "key" in current:
                mapping[current["source_label"]] = current["key"]
            current = {}
            k, v = raw[4:].split(":", 1)
            current[k.strip()] = str(_scalar(v))
        elif in_mapping and current is not None and raw.startswith("    ") and ":" in s:
            k, v = s.split(":", 1)
            current[k.strip()] = str(_scalar(v))
    if current and "source_label" in current and "key" in current:
        mapping[current["source_label"]] = current["key"]
    return IntakeProfile(
        effective_header_row=effective,
        preserve_group_header_row=preserve_group_header_row,
        mapping=mapping or dict(DEFAULT_MAPPING),
    )


def colnum(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref or "A1")
    if not letters:
        return 1
    n = 0
    for ch in letters.group():
        n = n * 26 + ord(ch) - 64
    return n


def _cell_value(cell, shared: list[str]):
    typ = cell.attrib.get("t")
    if typ == "inlineStr":
        return "".join(x.text or "" for x in cell.iter(f"{{{MAIN}}}t"))
    value = cell.find(f"{{{MAIN}}}v")
    raw = "" if value is None or value.text is None else value.text
    if typ == "s" and raw:
        return shared[int(raw)]
    if raw == "":
        return ""
    try:
        num = float(raw)
        return int(num) if num.is_integer() else num
    except ValueError:
        return raw


def read_xlsx_matrix(path: Path) -> tuple[str, list[list[object]]]:
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(f"{{{MAIN}}}t")) for si in root.findall(f"{{{MAIN}}}si")]
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        sheet = workbook.find(f".//{{{MAIN}}}sheet")
        if sheet is None:
            raise ValueError("XLSX contains no worksheet")
        sheet_name = sheet.attrib.get("name", "Sheet1")
        rid = sheet.attrib[f"{{{REL}}}id"]
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.attrib["Target"] for r in rels.findall(f"{{{PKGREL}}}Relationship") if r.attrib.get("Id") == rid)
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        root = ET.fromstring(z.read(target))
        matrix: list[list[object]] = []
        for row in root.findall(f".//{{{MAIN}}}row"):
            values = {colnum(c.attrib.get("r", "A1")): _cell_value(c, shared) for c in row.findall(f"{{{MAIN}}}c")}
            matrix.append([values.get(i, "") for i in range(1, max(values, default=0) + 1)])
        return sheet_name, matrix


def _clean(v) -> str:
    if v is None:
        return ""
    return str(v).replace("\u00a0", " ").strip()


def _raw(v) -> str:
    return "" if v is None else str(v)


def source_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def map_rows(matrix: list[list[object]], profile: IntakeProfile, source_file: str, sheet_name: str, file_hash: str):
    header_idx = profile.effective_header_row - 1
    if header_idx < 0 or header_idx >= len(matrix):
        raise ValueError(f"effective header row {profile.effective_header_row} is outside worksheet")
    headers = [_clean(x) for x in matrix[header_idx]]
    index_by_key: dict[str, int] = {}
    for i, label in enumerate(headers):
        if label in profile.mapping:
            index_by_key[profile.mapping[label]] = i
    missing_columns = sorted(REQUIRED - set(index_by_key))
    if missing_columns:
        raise ValueError(f"required source columns missing: {missing_columns}")

    records, invalid = [], []
    for matrix_idx in range(header_idx + 1, len(matrix)):
        row = matrix[matrix_idx]
        if not any(_clean(x) for x in row):
            continue
        mapped, raw_cells = {}, {}
        for key, col_idx in index_by_key.items():
            value = row[col_idx] if col_idx < len(row) else ""
            mapped[key] = _clean(value)
            raw_cells[key] = _raw(value)
        missing = sorted(k for k in REQUIRED if not mapped.get(k))
        excel_row = matrix_idx + 1
        if missing:
            invalid.append({
                "source_row": excel_row,
                "missing": missing,
                "external_requirement_id": mapped.get("external_requirement_id", ""),
                "status": "INVALID_ROW",
            })
            continue
        records.append({
            "source_record_id": f"SRCREQ-{len(records)+1:06d}",
            "source_file": source_file,
            "source_sheet": sheet_name,
            "source_row": excel_row,
            "source_hash": file_hash,
            **mapped,
            "raw": raw_cells,
        })
    return records, invalid


def group_key(record: dict) -> tuple[str, str, str]:
    return record["level1"], record["level2"], record["source_requirement_name"]


def stable_group_key(key: tuple[str, str, str]) -> str:
    payload = "\x1f".join(key).encode("utf-8")
    return "rqgrp:sha256:" + hashlib.sha256(payload).hexdigest()


def similarity_key(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", text.lower(), flags=re.UNICODE)


def transform(records: list[dict], invalid: list[dict] | None = None, similarity_threshold: float = 0.84) -> dict:
    invalid = list(invalid or [])
    groups, external_seen = {}, {}
    for r in records:
        groups.setdefault(group_key(r), []).append(r)
        external_seen.setdefault(r["external_requirement_id"], []).append(r["source_record_id"])
    duplicates = [
        {"external_requirement_id": ext, "source_record_ids": ids, "type": "DUPLICATE_EXTERNAL_ID"}
        for ext, ids in sorted(external_seen.items()) if len(ids) > 1
    ]

    rq_candidates, fr_candidates = [], []
    for idx, (key, members) in enumerate(groups.items(), 1):
        rq_id = f"RQ-CAND-{idx:04d}"
        rq_stable_key = stable_group_key(key)
        rq_candidates.append({
            "candidate_id": rq_id,
            "stable_key": rq_stable_key,
            "level1": key[0],
            "level2": key[1],
            "name": key[2],
            "source_record_ids": [m["source_record_id"] for m in members],
            "external_requirement_ids": [m["external_requirement_id"] for m in members],
            "current_problem": "OPEN",
            "desired_result_status": "INFERRED_CANDIDATE",
            "quality": "WARNING",
        })
        for member in members:
            fr_candidates.append({
                "candidate_id": f"FR-CAND-{len(fr_candidates)+1:05d}",
                "stable_key": f'external:{member["external_requirement_id"]}',
                "parent_rq_candidate_id": rq_id,
                "parent_rq_stable_key": rq_stable_key,
                "external_requirement_id": member["external_requirement_id"],
                "name": member["source_requirement_text"],
                "source_record_id": member["source_record_id"],
                "status": "CANDIDATE",
            })

    reviews = []
    for i, a in enumerate(rq_candidates):
        for b in rq_candidates[i + 1:]:
            if (a["level1"], a["level2"]) != (b["level1"], b["level2"]):
                continue
            sa, sb = similarity_key(a["name"]), similarity_key(b["name"])
            if not sa or not sb:
                continue
            score = difflib.SequenceMatcher(None, sa, sb).ratio()
            if score >= similarity_threshold:
                reviews.append({
                    "type": "GROUPING_REVIEW",
                    "candidate_a": a["candidate_id"],
                    "candidate_b": b["candidate_id"],
                    "stable_key_a": a["stable_key"],
                    "stable_key_b": b["stable_key"],
                    "name_a": a["name"],
                    "name_b": b["name"],
                    "similarity": round(score, 4),
                    "auto_merged": False,
                })

    alerts = []
    if rq_candidates:
        alerts.append({
            "type": "MISSING_BUSINESS_CONTEXT",
            "scope": "RQ_CANDIDATES",
            "count": len(rq_candidates),
            "fields": ["current_problem", "confirmed_desired_result", "business_rules"],
            "blocking": False,
        })
    alerts.extend({**d, "blocking": False} for d in duplicates)
    alerts.extend({**d, "blocking": False} for d in invalid)
    return {
        "schema_version": 2,
        "import_result": {
            "source_rows": len(records) + len(invalid),
            "imported_rows": len(records),
            "invalid_rows": len(invalid),
            "duplicate_external_ids": len(duplicates),
            "rq_candidate_count": len(rq_candidates),
            "fr_candidate_count": len(fr_candidates),
            "grouping_review_count": len(reviews),
            "non_blocking": True,
        },
        "source_records": records,
        "rq_candidates": rq_candidates,
        "fr_candidates": fr_candidates,
        "grouping_reviews": reviews,
        "alerts": alerts,
    }


def build_source_metadata(
    matrix: list[list[object]], profile: IntakeProfile, source_file: str, sheet_name: str, file_hash: str
) -> dict:
    header_idx = profile.effective_header_row - 1
    metadata = {
        "source_file": source_file,
        "source_sheet": sheet_name,
        "source_hash": file_hash,
        "effective_header_row": profile.effective_header_row,
        "effective_headers": [_raw(x) for x in matrix[header_idx]],
        "group_header_rows": [],
    }
    if profile.preserve_group_header_row:
        metadata["group_header_rows"] = [
            {"source_row": idx + 1, "values": [_raw(x) for x in matrix[idx]]}
            for idx in range(0, header_idx)
        ]
    return metadata


def render_report(data: dict, source_name: str) -> str:
    r = data["import_result"]
    lines = [
        "# 요구사항 Bulk Intake 결과",
        "",
        f"> Source: `{source_name}`",
        "",
        "```mermaid",
        "flowchart LR",
        f'    A["Source {r["source_rows"]} rows"] --> B["Imported {r["imported_rows"]}"]',
        f'    B --> C["RQ Candidates {r["rq_candidate_count"]}"]',
        f'    C --> D["FR Candidates {r["fr_candidate_count"]}"]',
        f'    D --> E["Grouping Reviews {r["grouping_review_count"]}"]',
        "```",
        "",
        "## Summary",
        "",
        "| 항목 | 건수 |",
        "|---|---:|",
        f'| 원본 행 | {r["source_rows"]} |',
        f'| Import 성공 | {r["imported_rows"]} |',
        f'| Invalid 행 | {r["invalid_rows"]} |',
        f'| 중복 외부 ID | {r["duplicate_external_ids"]} |',
        f'| RQ Candidate | {r["rq_candidate_count"]} |',
        f'| FR Candidate | {r["fr_candidate_count"]} |',
        f'| Grouping Review | {r["grouping_review_count"]} |',
        "",
        "## Grouping Review",
        "",
    ]
    if data["grouping_reviews"]:
        lines += ["| A | B | 유사도 | 자동병합 |", "|---|---|---:|---|"]
        for item in data["grouping_reviews"]:
            lines.append(f'| {item["name_a"]} | {item["name_b"]} | {item["similarity"]:.4f} | 아니오 |')
    else:
        lines.append("- 없음")
    lines += [
        "",
        "## 원칙",
        "",
        "- 유사 제목은 자동 병합하지 않는다.",
        "- Invalid/중복 행이 있어도 정상 행 Import는 계속한다.",
        "- 원문과 외부 요구사항 ID를 Source Record에 보존한다.",
        "- 재-import 비교용 stable key를 Candidate에 보존한다.",
        "- 설정된 경우 상위 그룹 Header도 Source Metadata에 보존한다.",
        "- Business Context가 부족하면 OPEN/Alert로 남긴다.",
        "",
    ]
    return "\n".join(lines)


def run_import(xlsx: Path, profile_path: Path | None, json_out: Path, report_out: Path | None) -> dict:
    profile = load_profile(profile_path)
    sheet, matrix = read_xlsx_matrix(xlsx)
    file_hash = source_hash(xlsx)
    records, invalid = map_rows(matrix, profile, xlsx.name, sheet, file_hash)
    data = transform(records, invalid)
    data["source_metadata"] = build_source_metadata(matrix, profile, xlsx.name, sheet, file_hash)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report_out:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_report(data, xlsx.name), encoding="utf-8")
    return data


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("xlsx")
    p.add_argument("--profile", default="sdlc/config/requirement-intake-columns.example.yaml")
    p.add_argument("--json-out", default="sdlc/canonical/intake/requirements-import.json")
    p.add_argument("--report-out", default="docs/00_관리/요구사항_인입결과.md")
    args = p.parse_args(argv)
    data = run_import(
        Path(args.xlsx),
        Path(args.profile) if args.profile else None,
        Path(args.json_out),
        Path(args.report_out) if args.report_out else None,
    )
    print(json.dumps(data["import_result"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
