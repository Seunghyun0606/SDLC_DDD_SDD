#!/usr/bin/env python3
"""Evidence-backed delivery status for the PM Human Control Plane.

No Stage or provenance record implies customer acceptance. Technical verification, acceptance,
deployment and AS-BUILT reconciliation are independent states with explicit evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = "sdlc/runtime/delivery-status"
EVENTS = [
    "DEVELOPMENT_STARTED", "SOURCE_CHANGED", "BUILD_PASSED", "TEST_PASSED", "REGRESSION_PASSED",
    "TECHNICAL_VERIFICATION_PASSED", "CUSTOMER_ACCEPTED", "DEPLOYMENT_COMPLETED", "AS_BUILT_RECONCILED"
]
EVIDENCE_REQUIRED = set(EVENTS) - {"DEVELOPMENT_STARTED"}


def now() -> str: return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def _safe(v: str) -> str: return re.sub(r"[^A-Za-z0-9_.-]+", "_", v).strip("_") or "RQ"
def _path(root: Path, target: str) -> Path: return root / ROOT / f"{_safe(target)}.json"
def _load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"schema_version": 1, "events": []}
def _save(path: Path, data: dict[str, Any]) -> None: path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(root: Path, target: str, event: str, evidence: str | None, actor: str | None = None) -> dict[str, Any]:
    event = event.upper()
    if event not in EVENTS: raise ValueError(f"unsupported delivery event: {event}")
    if event in EVIDENCE_REQUIRED and not str(evidence or "").strip(): raise ValueError(f"evidence required for {event}")
    path = _path(root, target); data = _load(path); data["target_id"] = target
    row = {"event": event, "evidence": evidence, "actor": actor, "recorded_at": now()}
    data.setdefault("events", []).append(row); _save(path, data); return row


def snapshot(root: Path, target: str) -> dict[str, Any]:
    data = _load(_path(root, target)); seen = {str(x.get("event")) for x in data.get("events") or []}
    def yes(event: str) -> bool: return event in seen
    return {
        "development_started": yes("DEVELOPMENT_STARTED"),
        "source_changed": yes("SOURCE_CHANGED"),
        "build_passed": yes("BUILD_PASSED"),
        "test_passed": yes("TEST_PASSED"),
        "regression_passed": yes("REGRESSION_PASSED"),
        "technical_verification_passed": yes("TECHNICAL_VERIFICATION_PASSED"),
        "customer_acceptance": "ACCEPTED" if yes("CUSTOMER_ACCEPTED") else "PENDING",
        "deployment_completed": yes("DEPLOYMENT_COMPLETED"),
        "as_built_reconciled": yes("AS_BUILT_RECONCILED"),
        "release_blocked": yes("DEVELOPMENT_STARTED") and not (yes("BUILD_PASSED") and yes("TEST_PASSED") and yes("REGRESSION_PASSED") and yes("TECHNICAL_VERIFICATION_PASSED") and yes("CUSTOMER_ACCEPTED")),
        "event_count": len(data.get("events") or []),
        "latest_evidence": [x.get("evidence") for x in (data.get("events") or [])[-5:] if x.get("evidence")],
        "acceptance_is_not_inferred_from_verify_stage": True,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("command", choices=["mark", "status"]); ap.add_argument("--root", default="."); ap.add_argument("--target", required=True); ap.add_argument("--event", choices=EVENTS); ap.add_argument("--evidence"); ap.add_argument("--actor")
    args = ap.parse_args(argv); root = Path(args.root).resolve()
    try:
        if args.command == "mark":
            if not args.event: raise ValueError("mark requires --event")
            result = {"status": "DELIVERY_EVENT_RECORDED", "event": record(root, args.target, args.event, args.evidence, args.actor), "delivery": snapshot(root, args.target)}
        else: result = {"status": "DELIVERY_STATUS", "target_id": args.target, "delivery": snapshot(root, args.target)}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
