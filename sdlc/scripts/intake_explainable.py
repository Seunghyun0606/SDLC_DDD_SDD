#!/usr/bin/env python3
"""Explainable Requirement Intake wrapper for v1.9.

The existing intake remains the authoritative parser/Canonical writer. This wrapper adds an RQ
Extraction Manifest so a PM can understand why each RQ was formed without opening runtime JSON.
After configured-project intake, the PM RQ worklist is refreshed as a non-authoritative View.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


INTAKE = _load("explainable_intake_core", "intake_requirements.py")


def _path(root: Path, raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


def _row_locator(row: dict[str, Any]) -> str:
    return f'{row.get("source_file", "source")}#{row.get("source_sheet", "Sheet1")}!row:{row.get("source_row", "OPEN")}'


def build_extraction_manifests(data: dict[str, Any]) -> dict[str, Any]:
    candidates = list(data.get("rq_candidates") or [])
    targets = list((data.get("canonical") or {}).get("rq_target_ids") or [])
    rows = {str(r.get("source_record_id")): r for r in data.get("source_records") or []}
    reviews = list(data.get("grouping_reviews") or [])
    manifests: dict[str, Any] = {}
    for index, candidate in enumerate(candidates):
        target = targets[index] if index < len(targets) else str(candidate.get("candidate_id") or f"RQ-CAND-{index+1}")
        candidate_id = str(candidate.get("candidate_id") or "")
        source_ids = [str(x) for x in candidate.get("source_record_ids") or []]
        source_rows = [rows[x] for x in source_ids if x in rows]
        similarity = [
            item for item in reviews
            if candidate_id in {str(item.get("candidate_a") or ""), str(item.get("candidate_b") or "")}
        ]
        manifests[target] = {
            "schema_version": 1,
            "rq_id": target,
            "grouping_rule_id": "INTAKE-EXACT-HIERARCHY-NAME",
            "grouping_rule_version": "1.0",
            "grouping_method": "EXACT_GROUP_BY",
            "grouping_basis": {
                "level1": candidate.get("level1"),
                "level2": candidate.get("level2"),
                "requirement_name": candidate.get("name"),
                "stable_key": candidate.get("stable_key"),
            },
            "source_rows": [r.get("source_row") for r in source_rows],
            "source_record_ids": source_ids,
            "source_locators": [_row_locator(r) for r in source_rows],
            "external_requirement_ids": list(candidate.get("external_requirement_ids") or []),
            "similarity_candidates": similarity,
            "auto_merge": False,
            "human_decision": "REVIEW_REQUIRED" if similarity else "NOT_REQUIRED_FOR_EXACT_GROUPING",
            "creation_reason": "Same Level1 + Level2 + requirement name rows are grouped; similar names are never auto-merged.",
        }
    return manifests


def render_manifest_report(manifests: dict[str, Any]) -> str:
    lines = [
        "# RQ Extraction Manifest",
        "",
        "## 문서 목적",
        "요구사항 원본 행이 왜 각 RQ로 묶였는지 PM/Reviewer가 Runtime JSON 없이 확인하는 View다.",
        "",
        "```mermaid",
        "flowchart LR",
        '    A["Requirement Source Rows"] --> B["Exact Grouping Rule"]',
        '    B --> C["RQ Candidate"]',
        '    C --> D{"Similar Candidate?"}',
        '    D -- "Yes" --> E["Human Review"]',
        '    D -- "No" --> F["RQ Work Target"]',
        '    E --> F',
        "```",
        "",
    ]
    for rq_id, manifest in manifests.items():
        basis = manifest["grouping_basis"]
        lines += [
            f"## {rq_id}",
            "",
            f'- 생성 이유: {manifest["creation_reason"]}',
            f'- Grouping Rule: `{manifest["grouping_rule_id"]}` v{manifest["grouping_rule_version"]}',
            f'- 기준: `{basis.get("level1")}` / `{basis.get("level2")}` / `{basis.get("requirement_name")}`',
            f'- 원본 행: {", ".join(str(x) for x in manifest["source_rows"]) or "없음"}',
            f'- External IDs: {", ".join(str(x) for x in manifest["external_requirement_ids"]) or "없음"}',
            f'- 유사 후보 검토: {len(manifest["similarity_candidates"])}건',
            f'- 자동 병합: {"예" if manifest["auto_merge"] else "아니오"}',
            f'- Human Decision: `{manifest["human_decision"]}`',
            "",
        ]
    return "\n".join(lines) + "\n"


def run(
    xlsx: Path,
    *,
    root: Path,
    profile_path: Path | None,
    json_out: Path,
    report_out: Path | None,
    store_path: Path,
    candidate_only: bool,
    manifest_json: Path,
    manifest_report: Path,
) -> dict[str, Any]:
    data = INTAKE.run_intake(
        xlsx,
        profile_path=profile_path,
        json_out=json_out,
        report_out=report_out,
        store_path=store_path,
        apply_to_canonical=not candidate_only,
    )
    manifests = build_extraction_manifests(data)
    manifest_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_json.write_text(json.dumps({"schema_version": 1, "requirements": manifests}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_report.parent.mkdir(parents=True, exist_ok=True)
    manifest_report.write_text(render_manifest_report(manifests), encoding="utf-8")
    return {"data": data, "manifests": manifests}


def _refresh_project_worklist(root: Path, candidate_only: bool) -> dict[str, Any] | None:
    if candidate_only or not (root / ".sdlc/project.yaml").is_file():
        return None
    try:
        worklist = _load("explainable_intake_rq_worklist", "rq_worklist.py")
        return worklist.refresh(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        # Management-view refresh must not roll back a successful Canonical intake.
        return {"status": "RQ_WORKLIST_REFRESH_REQUIRED", "error": str(exc), "next_command": "python sdlc/scripts/harness.py rq-list refresh"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Requirement intake with per-RQ extraction explainability.")
    ap.add_argument("xlsx")
    ap.add_argument("--root", default=".")
    ap.add_argument("--profile")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--json-out", default="sdlc/runtime/intake/requirements-import.json")
    ap.add_argument("--report-out", default="docs/00_관리/요구사항_인입결과.md")
    ap.add_argument("--manifest-json", default="sdlc/runtime/intake/rq-extraction-manifest.json")
    ap.add_argument("--manifest-report", default="docs/00_관리/RQ_생성근거.md")
    ap.add_argument("--candidate-only", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        xlsx = _path(root, args.xlsx)
        if not xlsx or not xlsx.is_file():
            raise ValueError(f"requirement file not found: {xlsx}")
        result = run(
            xlsx,
            root=root,
            profile_path=_path(root, args.profile),
            json_out=_path(root, args.json_out),
            report_out=_path(root, args.report_out),
            store_path=_path(root, args.store),
            candidate_only=args.candidate_only,
            manifest_json=_path(root, args.manifest_json),
            manifest_report=_path(root, args.manifest_report),
        )
        data = result["data"]
        targets = list((data.get("canonical") or {}).get("rq_target_ids") or [])
        worklist = _refresh_project_worklist(root, args.candidate_only)
        out = {
            "status": "INTAKE_READY_FOR_WORK" if targets else ("INTAKE_CANDIDATE_ONLY" if args.candidate_only else "INTAKE_NO_TARGET"),
            "import_result": data.get("import_result"),
            "canonical": data.get("canonical"),
            "first_target": targets[0] if targets else None,
            "rq_extraction_manifest": args.manifest_json,
            "human_manifest_report": args.manifest_report,
            "rq_worklist": worklist,
            "next_command": f"python sdlc/scripts/harness.py work --target {targets[0]}" if targets else None,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if targets or args.candidate_only else 3
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INTAKE_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
