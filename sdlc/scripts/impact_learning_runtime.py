#!/usr/bin/env python3
"""Historical Impact Learning for long-running SM/legacy maintenance.

Stores predicted vs confirmed actual impact separately. Unexpected discoveries become future
candidates with support evidence; they never become Business Truth or confirmed impact solely from
history. Candidate output is deliberately capped to prevent AI/context explosion.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STORE = "sdlc/runtime/impact-learning/history.json"
CHANGE_EVIDENCE_ROOT = "sdlc/runtime/change-level"
MAX_CANDIDATES = 10


def now() -> str: return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def _load(path: Path, default: Any) -> Any:
    if not path.is_file(): return default
    return json.loads(path.read_text(encoding="utf-8"))

def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _safe(value: str) -> str: return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "TARGET"

def _norm(items: list[str] | None) -> list[str]: return sorted(set(str(x).strip() for x in (items or []) if str(x).strip()))


def record_change(store: dict[str, Any], *, change_id: str, target_id: str, keys: list[str], predicted: list[str], actual: list[str], incident_refs: list[str] | None = None, fix_refs: list[str] | None = None) -> dict[str, Any]:
    predicted_set, actual_set = set(_norm(predicted)), set(_norm(actual))
    row = {
        "change_id": change_id,
        "target_id": target_id,
        "business_keys": _norm(keys),
        "predicted_impact": sorted(predicted_set),
        "confirmed_actual_impact": sorted(actual_set),
        "false_positive": sorted(predicted_set - actual_set),
        "unexpected_discovery": sorted(actual_set - predicted_set),
        "incident_refs": _norm(incident_refs),
        "fix_refs": _norm(fix_refs),
        "recorded_at": now(),
        "history_is_candidate_authority_only": True,
    }
    records = store.setdefault("records", [])
    existing = next((x for x in records if x.get("change_id") == change_id and x.get("target_id") == target_id), None)
    if existing: existing.clear(); existing.update(row)
    else: records.append(row)
    return row


def recommend(store: dict[str, Any], keys: list[str], *, limit: int = MAX_CANDIDATES) -> list[dict[str, Any]]:
    requested = set(_norm(keys)); scores: dict[str, dict[str, Any]] = {}
    for row in store.get("records") or []:
        row_keys = set(row.get("business_keys") or [])
        overlap = len(requested & row_keys) if requested else 0
        if requested and not overlap: continue
        for component in row.get("confirmed_actual_impact") or []:
            item = scores.setdefault(component, {"component_id": component, "support_count": 0, "unexpected_support_count": 0, "supporting_changes": [], "key_overlap": 0})
            item["support_count"] += 1; item["key_overlap"] += overlap; item["supporting_changes"].append(row.get("change_id"))
            if component in set(row.get("unexpected_discovery") or []): item["unexpected_support_count"] += 1
    ranked = sorted(scores.values(), key=lambda x: (-int(x["key_overlap"]), -int(x["unexpected_support_count"]), -int(x["support_count"]), str(x["component_id"])))[: max(0, min(int(limit), MAX_CANDIDATES))]
    for item in ranked:
        item["status"] = "HISTORICAL_IMPACT_CANDIDATE"; item["confirmed_current_impact"] = False; item["requires_current_evidence"] = True; item["supporting_changes"] = sorted(set(str(x) for x in item["supporting_changes"] if x))
    return ranked


def capture_discovery(root: Path, store: dict[str, Any], *, change_id: str, target_id: str, component_id: str, keys: list[str] | None = None) -> dict[str, Any]:
    records = store.setdefault("records", [])
    row = next((x for x in records if x.get("change_id") == change_id and x.get("target_id") == target_id), None)
    if not row:
        row = record_change(store, change_id=change_id, target_id=target_id, keys=keys or [], predicted=[], actual=[component_id])
    else:
        actual = set(row.get("confirmed_actual_impact") or []); actual.add(component_id)
        predicted = set(row.get("predicted_impact") or [])
        row["confirmed_actual_impact"] = sorted(actual); row["false_positive"] = sorted(predicted - actual); row["unexpected_discovery"] = sorted(actual - predicted); row["recorded_at"] = now()
        if keys: row["business_keys"] = _norm(list(row.get("business_keys") or []) + keys)
    # Feed only typed technical evidence back into Change Level. This does not create Business Truth.
    evidence_path = root / CHANGE_EVIDENCE_ROOT / f"{_safe(target_id)}-evidence.json"
    evidence = _load(evidence_path, {"facts": {}, "evidence_refs": []})
    facts = evidence.setdefault("facts", {})
    count = len(set(row.get("confirmed_actual_impact") or []) | set(row.get("predicted_impact") or []))
    facts["CHANGED_COMPONENT_COUNT"] = max(int(facts.get("CHANGED_COMPONENT_COUNT") or 0), count)
    facts["IMPACT_COVERAGE"] = "PARTIAL"
    evidence["evidence_refs"] = _norm(list(evidence.get("evidence_refs") or []) + [f"historical-discovery:{change_id}:{component_id}"])
    evidence.setdefault("unexpected_discoveries", []).append({"change_id": change_id, "component_id": component_id, "captured_at": now()})
    _save(evidence_path, evidence)
    return {"status": "DISCOVERY_CAPTURED", "change_id": change_id, "target_id": target_id, "component_id": component_id, "actual_impact_count": count, "change_level_evidence": evidence_path.relative_to(root).as_posix(), "business_truth_mutated": False}


def metrics(row: dict[str, Any]) -> dict[str, Any]:
    predicted, actual = set(row.get("predicted_impact") or []), set(row.get("confirmed_actual_impact") or [])
    tp = len(predicted & actual); precision = tp / len(predicted) if predicted else (1.0 if not actual else 0.0); recall = tp / len(actual) if actual else 1.0
    return {"impact_recall": recall, "impact_precision": precision, "missed_impact": len(actual - predicted), "false_positive": len(predicted - actual), "unexpected_discovery": len(actual - predicted)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("command", choices=["record", "recommend", "discover", "metrics"]); ap.add_argument("--root", default="."); ap.add_argument("--store", default=DEFAULT_STORE); ap.add_argument("--change"); ap.add_argument("--target"); ap.add_argument("--key", action="append", default=[]); ap.add_argument("--predicted", action="append", default=[]); ap.add_argument("--actual", action="append", default=[]); ap.add_argument("--component"); ap.add_argument("--limit", type=int, default=MAX_CANDIDATES)
    args = ap.parse_args(argv); root = Path(args.root).resolve(); path = Path(args.store); path = path if path.is_absolute() else root / path; store = _load(path, {"schema_version": 1, "records": []})
    try:
        if args.command == "record":
            if not args.change or not args.target: raise ValueError("record requires --change and --target")
            row = record_change(store, change_id=args.change, target_id=args.target, keys=args.key, predicted=args.predicted, actual=args.actual); _save(path, store); result = {"status": "IMPACT_HISTORY_RECORDED", "record": row, "metrics": metrics(row)}
        elif args.command == "recommend": result = {"status": "HISTORICAL_CANDIDATES", "candidates": recommend(store, args.key, limit=args.limit), "candidate_limit": MAX_CANDIDATES}
        elif args.command == "discover":
            if not args.change or not args.target or not args.component: raise ValueError("discover requires --change --target --component")
            result = capture_discovery(root, store, change_id=args.change, target_id=args.target, component_id=args.component, keys=args.key); _save(path, store)
        else:
            if not args.change or not args.target: raise ValueError("metrics requires --change --target")
            row = next((x for x in store.get("records") or [] if x.get("change_id") == args.change and x.get("target_id") == args.target), None)
            if not row: raise ValueError("impact history record not found")
            result = {"status": "IMPACT_METRICS", **metrics(row)}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
