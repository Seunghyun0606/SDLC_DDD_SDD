#!/usr/bin/env python3
"""Projection lifecycle: affected -> STALE_VIEW -> regenerate -> review -> CURRENT.

Generated Customer/PM views are never Business Truth. Human edits that imply policy changes are
captured as decision candidates and require the normal review workflow before Canonical mutation.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = "sdlc/runtime/projections"


def now() -> str: return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def _safe(v: str) -> str: return re.sub(r"[^A-Za-z0-9_.-]+", "_", v).strip("_") or "VIEW"
def _load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
def _save(path: Path, data: dict[str, Any]) -> None: path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def canonical_revision(root: Path) -> int:
    data = _load(root / "sdlc/canonical/store.json"); return int(data.get("revision") or 0)

def metadata_path(root: Path, target: str, artifact_id: str) -> Path: return root / ROOT / f"{_safe(target)}-{_safe(artifact_id)}.json"


def register_generated(root: Path, *, target: str, artifact_id: str, artifact_path: str, audience: str, profile_id: str | None = None) -> dict[str, Any]:
    revision = canonical_revision(root); audience = audience.upper()
    row = {
        "schema_version": 2, "target_id": target, "artifact_id": artifact_id, "artifact_path": artifact_path,
        "audience": audience, "profile_id": profile_id, "generated_from_revision": revision, "generated_at": now(),
        "lifecycle": "PENDING_REVIEW" if audience in {"CUSTOMER", "PM_REVIEW"} else "CURRENT",
        "reviewed_revision": None if audience in {"CUSTOMER", "PM_REVIEW"} else revision,
        "business_truth_authority": False if audience == "CUSTOMER" else None,
        "decision_candidate": None,
    }
    _save(metadata_path(root, target, artifact_id), row); return row


def state(root: Path, row: dict[str, Any]) -> str:
    revision = canonical_revision(root); generated = int(row.get("generated_from_revision") or 0)
    if revision > generated: return "STALE_VIEW"
    return str(row.get("lifecycle") or "CURRENT").upper()


def affected(root: Path, target: str | None = None) -> list[dict[str, Any]]:
    base = root / ROOT; rows: list[dict[str, Any]] = []
    if not base.is_dir(): return rows
    for path in sorted(base.glob("*.json")):
        try: row = _load(path)
        except (OSError, json.JSONDecodeError): continue
        if target and str(row.get("target_id")) != target: continue
        rows.append({**row, "metadata_path": path.relative_to(root).as_posix(), "state": state(root, row)})
    return rows


def review(root: Path, *, target: str, artifact_id: str, reviewer: str, accepted: bool, business_policy_edit: str | None = None) -> dict[str, Any]:
    path = metadata_path(root, target, artifact_id); row = _load(path)
    if not row: raise ValueError("projection metadata not found")
    current_revision = canonical_revision(root)
    if int(row.get("generated_from_revision") or 0) < current_revision:
        return {"status": "STALE_VIEW", "current": False, "regeneration_required": True, "canonical_mutated": False}
    if business_policy_edit:
        row["lifecycle"] = "DECISION_REQUIRED"; row["decision_candidate"] = {"proposed_by": reviewer, "text": business_policy_edit, "captured_at": now(), "canonical_auto_apply": False}
        _save(path, row)
        return {"status": "DECISION_REQUIRED", "customer_view_current": False, "canonical_mutated": False, "review_workflow_required": True}
    row["lifecycle"] = "CURRENT" if accepted else "REVIEW_REJECTED"; row["reviewed_revision"] = current_revision if accepted else None; row["reviewer"] = reviewer; row["reviewed_at"] = now(); _save(path, row)
    return {"status": row["lifecycle"], "customer_view_current": bool(accepted), "canonical_mutated": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("command", choices=["generated", "status", "review"]); ap.add_argument("--root", default="."); ap.add_argument("--target"); ap.add_argument("--artifact-id"); ap.add_argument("--artifact-path"); ap.add_argument("--audience"); ap.add_argument("--profile-id"); ap.add_argument("--reviewer"); ap.add_argument("--accept", action="store_true"); ap.add_argument("--business-policy-edit")
    args = ap.parse_args(argv); root = Path(args.root).resolve()
    try:
        if args.command == "generated":
            if not all([args.target, args.artifact_id, args.artifact_path, args.audience]): raise ValueError("generated requires target/artifact-id/artifact-path/audience")
            result = {"status": "PROJECTION_GENERATED", "projection": register_generated(root, target=args.target, artifact_id=args.artifact_id, artifact_path=args.artifact_path, audience=args.audience, profile_id=args.profile_id)}
        elif args.command == "status": result = {"status": "PROJECTION_STATUS", "canonical_revision": canonical_revision(root), "views": affected(root, args.target)}
        else:
            if not all([args.target, args.artifact_id, args.reviewer]): raise ValueError("review requires target/artifact-id/reviewer")
            result = review(root, target=args.target, artifact_id=args.artifact_id, reviewer=args.reviewer, accepted=args.accept, business_policy_edit=args.business_policy_edit)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
