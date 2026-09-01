#!/usr/bin/env python3
"""Generate review-only reusable Knowledge candidates from verified Canonical evidence.

No Business Truth is auto-promoted. This runtime only selects entities with strong
provenance and writes a candidate artifact for human review, making KNOWLEDGE_PROMOTION
an executable step rather than a documentation-only aspiration.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("knowledge_apply", SCRIPT_DIR / "apply_canonical_delta.py")
APPLY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(APPLY)

REUSABLE_TYPES = {"BR", "DATA", "API", "NFR", "STD", "PROC"}


def candidates(store: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for entity_id, entity in sorted(store.get("entities", {}).items()):
        if entity.get("entity_type") not in REUSABLE_TYPES:
            continue
        provenance = entity.get("provenance", [])
        strong = [p for p in provenance if p.get("evidence_class") == "CONFIRMED" or p.get("stage") == "VERIFY"]
        if not strong:
            continue
        rows.append({
            "id": entity_id,
            "entity_type": entity.get("entity_type"),
            "truth_status": entity.get("truth_status"),
            "fields": entity.get("fields", {}),
            "evidence_count": len(provenance),
            "promotion_basis": strong[-3:],
            "review_required": True,
            "auto_apply": False,
        })
    return rows


def run(store_path: Path, artifact_path: Path) -> dict[str, Any]:
    store = APPLY.load_store(store_path)
    rows = candidates(store)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 재사용 지식 승격 후보", "", "> 자동 승격하지 않는다. 반복 사용 가치와 권위를 사람이 검토한 뒤 별도 변경으로 반영한다.", ""]
    if not rows:
        lines.append("현재 승격 후보가 없습니다.")
    for row in rows:
        lines += [f"## {row['id']} ({row['entity_type']})", f"- 현재 상태: {row['truth_status']}", f"- 근거 수: {row['evidence_count']}", "- 내용:", "```json", json.dumps(row["fields"], ensure_ascii=False, indent=2), "```", ""]
    artifact_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"status": "CANDIDATES_READY", "candidate_count": len(rows), "artifact_path": str(artifact_path), "review_required": True, "auto_apply": False, "candidates": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate review-only reusable Knowledge candidates.")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--output", default="sdlc/runtime/knowledge/promotion-candidates.md")
    ap.add_argument("--result-out")
    args = ap.parse_args(argv)
    try:
        result = run(Path(args.store), Path(args.output))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "FAILED", "error": str(exc)}
    if args.result_out:
        out = Path(args.result_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ["status", "candidate_count", "artifact_path", "review_required"]}, ensure_ascii=False))
    return 0 if result.get("status") == "CANDIDATES_READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
