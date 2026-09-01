#!/usr/bin/env python3
"""Capture an explicit customer review/decision back into Canonical provenance.

Rendering a customer document never creates new Business Truth. This reverse path also
stays conservative: ACCEPT/REJECT/REQUEST_CHANGE is recorded as CONFIRMED provenance.
Actual business-field mutation requires both `field_updates` in the decision input and the
explicit `--apply-business-change` flag.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("customer_decision_apply", SCRIPT_DIR / "apply_canonical_delta.py")
APPLY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(APPLY)

ALLOWED = {"ACCEPT", "REJECT", "REQUEST_CHANGE", "ACKNOWLEDGE"}
SAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def capture(root: Path, decision: dict[str, Any], *, store_path: Path, apply_business_change: bool = False) -> dict[str, Any]:
    root = root.resolve()
    required = ["decision_id", "target_id", "decision", "decided_by", "source_document"]
    missing = [key for key in required if not str(decision.get(key) or "").strip()]
    if missing:
        raise ValueError(f"missing customer decision fields: {missing}")
    verdict = str(decision["decision"]).upper()
    if verdict not in ALLOWED:
        raise ValueError(f"decision must be one of {sorted(ALLOWED)}")
    store = APPLY.load_store(store_path)
    target_id = str(decision["target_id"])
    entity = store.get("entities", {}).get(target_id)
    if not entity:
        raise ValueError(f"target not found in Canonical: {target_id}")

    safe = SAFE.sub("_", str(decision["decision_id"])).strip("_") or "decision"
    artifact_rel = f"sdlc/runtime/customer-decisions/{safe}.md"
    artifact = root / artifact_rel
    artifact.parent.mkdir(parents=True, exist_ok=True)
    note = str(decision.get("note") or "")
    artifact.write_text(
        f"# 고객 검토 결과 {decision['decision_id']}\n\n"
        f"- 대상: {target_id}\n- 결과: {verdict}\n- 확인자: {decision['decided_by']}\n"
        f"- 근거 문서: {decision['source_document']}\n- 의견: {note or '-'}\n",
        encoding="utf-8",
    )
    operations: list[dict[str, Any]] = [{
        "op": "ADD_PROVENANCE",
        "id": target_id,
        "evidence_class": "CONFIRMED",
        "locator": str(decision["source_document"]),
        "note": f"CUSTOMER_DECISION {verdict}; decided_by={decision['decided_by']}; {note}".strip(),
    }]
    updates = decision.get("field_updates")
    if updates:
        if not isinstance(updates, dict):
            raise ValueError("field_updates must be an object")
        if not apply_business_change:
            return {
                "status": "REVIEW_RECORDED_BUT_BUSINESS_CHANGE_NOT_APPLIED",
                "target_id": target_id,
                "artifact_path": artifact_rel,
                "required_action": "re-run with --apply-business-change after explicit authority confirmation",
                "pending_field_updates": updates,
            }
        operations.insert(0, {
            "op": "UPSERT_ENTITY",
            "id": target_id,
            "entity_type": entity.get("entity_type"),
            "fields": updates,
            "evidence_class": "CONFIRMED",
            "truth_status": "CONFIRMED_BUSINESS",
            "locator": str(decision["source_document"]),
            "note": f"Explicit customer business decision {decision['decision_id']}",
        })
    delta = {
        "schema_version": 1,
        "delta_id": f"CUSTOMER-{safe}",
        "base_revision": store["revision"],
        "stage": "CHANGE",
        "source_artifact": artifact_rel,
        "operations": operations,
    }
    result, _ = APPLY.apply_delta_to_store(store_path, delta)
    return {"status": result["status"], "target_id": target_id, "decision": verdict, "artifact_path": artifact_rel, "canonical_result": result}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Capture explicit customer document review into Canonical provenance.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--input", required=True, help="Customer decision JSON")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--apply-business-change", action="store_true")
    ap.add_argument("--output")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    store = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    try:
        decision = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = capture(root, decision, store_path=store, apply_business_change=args.apply_business_change)
    except (OSError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
        result = {"status": "FAILED", "error": str(exc)}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("status") in {"APPLIED", "IDEMPOTENT", "REVIEW_RECORDED_BUT_BUSINESS_CHANGE_NOT_APPLIED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
