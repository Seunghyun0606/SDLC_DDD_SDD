#!/usr/bin/env python3
"""Record the small set of human decisions surfaced by /work.

Users do not prepare decision JSON. This facade reuses ``capture_customer_decision.py``
and deliberately never applies business field mutations itself. A confirmed answer becomes
CONFIRMED provenance that the next Agent run can consume; field changes still go through
normal /work or /change safety guards.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CAPTURE = _load("wp4_customer_decision", "capture_customer_decision.py")


def _handoff_path(root: Path, target: str) -> Path:
    import re
    safe = re.sub(r"[^0-9A-Za-z가-힣_.-]+", "_", target).strip("_.-") or "TARGET"
    return root / "sdlc/runtime/work-handoff" / f"{safe}.json"


def _load_handoff(root: Path, target: str) -> dict:
    path = _handoff_path(root, target)
    if not path.is_file():
        raise ValueError(f"work handoff not found for {target}; run harness.py work --target {target} first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("target") != target:
        raise ValueError(f"invalid work handoff for {target}")
    if not str(data.get("document") or "").strip():
        raise ValueError(f"work handoff has no user document for {target}")
    return data


def _decision_from_args(args) -> tuple[str, str]:
    selected = [
        ("ACCEPT", "", bool(args.approve)),
        ("ACKNOWLEDGE", str(args.answer or "").strip(), args.answer is not None),
        ("REQUEST_CHANGE", str(args.request_change or "").strip(), args.request_change is not None),
        ("REJECT", str(args.reject or "").strip(), args.reject is not None),
    ]
    active = [(decision, note) for decision, note, enabled in selected if enabled]
    if len(active) != 1:
        raise ValueError("choose exactly one: --approve, --answer, --request-change, or --reject")
    decision, note = active[0]
    if decision != "ACCEPT" and not note:
        raise ValueError(f"{decision} requires non-empty decision text")
    return decision, note


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Confirm only the human-authority items surfaced by /work.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--by", required=True, help="Name or project role that made the decision")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--approve", action="store_true", help="Approve the generated document as reviewed")
    choice.add_argument("--answer", help="Provide a policy/scope/approval/technical-choice answer")
    choice.add_argument("--request-change", help="Request a concrete change with the reason/content")
    choice.add_argument("--reject", help="Reject with a concrete reason")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store_path = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    try:
        handoff = _load_handoff(root, args.target)
        decision, note = _decision_from_args(args)
        decision_id = "WORK-REVIEW-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        payload = {
            "decision_id": decision_id,
            "target_id": args.target,
            "decision": decision,
            "decided_by": args.by,
            "source_document": handoff["document"],
            "note": note,
        }
        captured = CAPTURE.capture(root, payload, store_path=store_path, apply_business_change=False)
    except (OSError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
        print(json.dumps({"status": "REVIEW_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if decision in {"ACCEPT", "ACKNOWLEDGE"}:
        next_command = f"python sdlc/scripts/harness.py work --target {args.target}"
        message = "검토 결과를 근거로 기록했습니다. Business Truth 필드를 자동 변경하지 않았으며 Agent가 다음 작업에서 이 결정을 근거로 사용합니다."
    else:
        quoted = shlex.quote(note)
        next_command = f"python sdlc/scripts/harness.py change --target {args.target} --change {quoted}"
        message = "변경/거절 사유를 근거로 기록했습니다. 자동 수정하지 않고 /change 경로로 넘깁니다."

    output = {
        "status": "REVIEW_RECORDED",
        "target": args.target,
        "document": handoff["document"],
        "decision": decision,
        "review_record": captured.get("artifact_path"),
        "canonical_status": (captured.get("canonical_result") or {}).get("status") or captured.get("status"),
        "business_fields_auto_changed": False,
        "next_command": next_command,
        "message": message,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
