#!/usr/bin/env python3
"""Dependency-light XLSX -> requirement intake adapter.

Reads OOXML directly so the harness does not require a spreadsheet desktop/runtime.
The adapter preserves workbook rows as GIVEN source records and never creates canonical RQ IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import yaml

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalized(value: Any) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", "", text.replace("\u00a0", " ")).casefold()


def col_index(ref: str) -> int:
    letters = re.match(r"([A-Z]+)", ref or "")
    if not letters:
        raise ValueError(f"invalid cell reference: {ref}")
    value = 0
    for ch in letters.group(1):
        value = value * 26 + (ord(ch) - 64)
    return value - 1


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    values: list[str] = []
    for si in root.findall(f"{{{NS_MAIN}}}si"):
        pieces = [node.text or "" for node in si.iter(f"{{{NS_MAIN}}}t")]
        values.append("".join(pieces))
    return values


def worksheet_target(zf: zipfile.ZipFile, sheet_name: str | None) -> tuple[str, str]:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall(f"{{{NS_PKG_REL}}}Relationship")}
    sheets = wb.find(f"{{{NS_MAIN}}}sheets")
    if sheets is None:
        raise ValueError("workbook contains no sheets")
    selected = None
    for sheet in sheets.findall(f"{{{NS_MAIN}}}sheet"):
        if sheet_name is None or sheet.attrib.get("name") == sheet_name:
            selected = sheet
            break
    if selected is None:
        raise ValueError(f"worksheet not found: {sheet_name}")
    rid = selected.attrib[f"{{{NS_REL}}}id"]
    target = rel_map[rid]
    if target.startswith("/"):
        path = target.lstrip("/")
    else:
        path = "xl/" + target.lstrip("/")
    path = re.sub(r"/\./", "/", path)
    return selected.attrib.get("name") or "Sheet1", path


def cell_value(cell: ET.Element, shared: list[str]) -> Any:
    ctype = cell.attrib.get("t")
    if ctype == "inlineStr":
        return "".join((n.text or "") for n in cell.iter(f"{{{NS_MAIN}}}t"))
    value = cell.find(f"{{{NS_MAIN}}}v")
    if value is None or value.text is None:
        return None
    raw = value.text
    if ctype == "s":
        idx = int(raw)
        return shared[idx] if 0 <= idx < len(shared) else raw
    if ctype == "b":
        return raw == "1"
    if ctype in {"str", "e"}:
        return raw
    try:
        num = float(raw)
        return int(num) if num.is_integer() else num
    except ValueError:
        return raw


def read_rows(path: Path, sheet_name: str | None) -> tuple[str, list[list[Any]]]:
    with zipfile.ZipFile(path) as zf:
        shared = shared_strings(zf)
        resolved_name, target = worksheet_target(zf, sheet_name)
        root = ET.fromstring(zf.read(target))
        sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
        if sheet_data is None:
            return resolved_name, []
        rows: list[list[Any]] = []
        max_col = 0
        sparse: list[dict[int, Any]] = []
        for row in sheet_data.findall(f"{{{NS_MAIN}}}row"):
            values: dict[int, Any] = {}
            for cell in row.findall(f"{{{NS_MAIN}}}c"):
                idx = col_index(cell.attrib.get("r", ""))
                values[idx] = cell_value(cell, shared)
                max_col = max(max_col, idx)
            sparse.append(values)
        for values in sparse:
            rows.append([values.get(i) for i in range(max_col + 1)])
        return resolved_name, rows


def detect_headers(rows: list[list[Any]], config: dict[str, Any]) -> tuple[int, dict[str, int]]:
    aliases = config.get("aliases") or {}
    required = set(config.get("required_fields") or [])
    scan_rows = min(int(config.get("header_scan_rows", 10)), len(rows))
    best: tuple[int, int, dict[str, int]] | None = None
    for ridx in range(scan_rows):
        mapping: dict[str, int] = {}
        for cidx, value in enumerate(rows[ridx]):
            token = normalized(value)
            if not token:
                continue
            for field, names in aliases.items():
                if field in mapping:
                    continue
                candidates = [normalized(x) for x in names or []]
                if any(token == alias or token.endswith(alias) for alias in candidates if alias):
                    mapping[field] = cidx
        score = len(mapping)
        if required.issubset(mapping):
            if best is None or score > best[0]:
                best = (score, ridx, mapping)
    if best is None:
        raise ValueError(f"required requirement headers not found: {sorted(required)}")
    return best[1], best[2]


def row_get(row: list[Any], mapping: dict[str, int], field: str) -> Any:
    idx = mapping.get(field)
    return row[idx] if idx is not None and idx < len(row) else None


def intake(path: Path, config: dict[str, Any], sheet_name: str | None = None, only_ids: set[str] | None = None) -> dict[str, Any]:
    worksheet, rows = read_rows(path, sheet_name)
    header_idx, mapping = detect_headers(rows, config)
    required = list(config.get("required_fields") or [])
    records = []
    all_ids = []
    skipped = []
    for source_row, row in enumerate(rows[header_idx + 1 :], start=header_idx + 2):
        record = {field: row_get(row, mapping, field) for field in (config.get("field_order") or mapping.keys())}
        if all(record.get(field) in {None, ""} for field in required):
            continue
        missing = [field for field in required if record.get(field) in {None, ""}]
        if missing:
            skipped.append({"source_row": source_row, "reason": "MISSING_REQUIRED_FIELD", "fields": missing})
            continue
        source_id = str(record["source_requirement_id"]).strip()
        all_ids.append(source_id)
        if only_ids and source_id not in only_ids:
            continue
        record["source_requirement_id"] = source_id
        records.append({
            "source_row": source_row,
            "truth_state": "GIVEN",
            **record,
        })

    duplicates = sorted([rid for rid, count in Counter(all_ids).items() if count > 1])
    level2_counts = Counter(str(row_get(row, mapping, "level2")) for row in rows[header_idx + 1 :] if row_get(row, mapping, "source_requirement_id"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "artifact_type": "REQUIREMENT_INTAKE",
        "requirement_intake": {
            "source": {
                "file_name": path.name,
                "source_revision": f"sha256:{digest}",
                "worksheet": worksheet,
                "header_row": header_idx + 1,
                "adapter": "XLSX_OOXML_DIRECT",
            },
            "header_mapping": {field: idx + 1 for field, idx in mapping.items()},
            "source_row_count": len(all_ids),
            "selected_count": len(records),
            "duplicate_source_requirement_ids": duplicates,
            "skipped_rows": skipped,
            "summary": {
                "level2_counts": dict(sorted(level2_counts.items())),
            },
            "records": records,
            "truth_guards": {
                "source_rows_are_given_not_canonical": True,
                "canonical_rq_must_not_be_created_by_intake": True,
                "missing_cells_must_not_be_invented": True,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("--config", type=Path, default=Path("sdlc/config/requirement-intake.yaml"))
    parser.add_argument("--sheet")
    parser.add_argument("--only-id", action="append", default=[])
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = intake(args.xlsx, load_yaml(args.config), args.sheet, set(args.only_id) or None)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    root = result["requirement_intake"]
    return 1 if root["duplicate_source_requirement_ids"] or root["skipped_rows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
