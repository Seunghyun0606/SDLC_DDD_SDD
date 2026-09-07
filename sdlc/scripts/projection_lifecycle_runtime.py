#!/usr/bin/env python3
"""Shared projection lifecycle for Engineering/Customer/PM views.

Canonical meaning remains authoritative.  Projection files may become stale or may be manually
edited, but neither condition mutates Canonical automatically.  Customer FINAL_REVIEW preserves the
reviewed human wording; a later Canonical revision marks that view STALE_VIEW instead of overwriting
it.  This is lifecycle metadata, not a new workflow engine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = "sdlc/runtime/projections"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _safe(v: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", v).strip("_") or "VIEW"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_revision(root: Path) -> int:
    data = _load(root / "sdlc/canonical/store.json")
    return int(data.get("revision") or 0)


def metadata_path(root: Path, target: str, artifact_id: str) -> Path:
    return root / ROOT / f"{_safe(target)}-{_safe(artifact_id)}.json"


def register_generated(
    root: Path,
    *,
    target: str,
    artifact_id: str,
    artifact_path: str,
    audience: str,
    profile_id: str | None = None,
    manual_edit_policy: str | None = None,
) -> dict[str, Any]:
    revision = canonical_revision(root)
    audience = audience.upper()
    default_edit = "FINAL_REVIEW_ONLY" if audience == "CUSTOMER" else "TYPO_ONLY" if audience in {"ENGINEERING", "INTERNAL_IT"} else "REVIEW_ONLY"
    artifact_abs = root / artifact_path
    row = {
        "schema_version": 3,
        "target_id": target,
        "artifact_id": artifact_id,
        "artifact_path": artifact_path,
        "audience": audience,
        "profile_id": profile_id,
        "generated_from_revision": revision,
        "generated_at": now(),
        "generated_content_hash": _hash(artifact_abs),
        "manual_edit_policy": str(manual_edit_policy or default_edit).upper(),
        "semantic_owner": "CANONICAL",
        "projection_owner": "AGENT",
        "lifecycle": "PENDING_REVIEW" if audience in {"CUSTOMER", "PM_REVIEW"} else "CURRENT",
        "reviewed_revision": None if audience in {"CUSTOMER", "PM_REVIEW"} else revision,
        "reviewed_content_hash": None,
        "business_truth_authority": False,
        "decision_candidate": None,
    }
    _save(metadata_path(root, target, artifact_id), row)
    return row


def _manual_edit_state(root: Path, row: dict[str, Any]) -> str | None:
    artifact_path = str(row.get("artifact_path") or "")
    if not artifact_path:
        return None
    current_hash = _hash(root / artifact_path)
    if current_hash is None:
        return "MISSING_PROJECTION"
    lifecycle = str(row.get("lifecycle") or "CURRENT").upper()
    reviewed_hash = row.get("reviewed_content_hash")
    generated_hash = row.get("generated_content_hash")
    if lifecycle == "FINAL_REVIEW" and reviewed_hash:
        return None if current_hash == reviewed_hash else "MANUAL_EDIT_DETECTED"
    if generated_hash and current_hash != generated_hash:
        return "MANUAL_EDIT_DETECTED"
    return None


def state(root: Path, row: dict[str, Any]) -> str:
    revision = canonical_revision(root)
    generated = int(row.get("generated_from_revision") or 0)
    if revision > generated:
        return "STALE_VIEW"
    edit_state = _manual_edit_state(root, row)
    if edit_state:
        return edit_state
    return str(row.get("lifecycle") or "CURRENT").upper()


def affected(root: Path, target: str | None = None) -> list[dict[str, Any]]:
    base = root / ROOT
    rows: list[dict[str, Any]] = []
    if not base.is_dir():
        return rows
    for path in sorted(base.glob("*.json")):
        try:
            row = _load(path)
        except (OSError, json.JSONDecodeError):
            continue
        if target and str(row.get("target_id")) != target:
            continue
        rows.append({
            **row,
            "metadata_path": path.relative_to(root).as_posix(),
            "state": state(root, row),
            "canonical_auto_mutation": False,
        })
    return rows


def review(
    root: Path,
    *,
    target: str,
    artifact_id: str,
    reviewer: str,
    accepted: bool,
    business_policy_edit: str | None = None,
    final_review: bool = False,
) -> dict[str, Any]:
    path = metadata_path(root, target, artifact_id)
    row = _load(path)
    if not row:
        raise ValueError("projection metadata not found")
    current_revision = canonical_revision(root)
    artifact_hash = _hash(root / str(row.get("artifact_path") or ""))
    if int(row.get("generated_from_revision") or 0) < current_revision:
        reviewed_hash = row.get("reviewed_content_hash")
        return {
            "status": "STALE_VIEW",
            "current": False,
            "regeneration_required": True,
            "canonical_mutated": False,
            "final_human_edit_exists": bool(row.get("lifecycle") == "FINAL_REVIEW" and reviewed_hash),
            "automatic_overwrite_allowed": False,
        }
    if business_policy_edit:
        row["lifecycle"] = "DECISION_REQUIRED"
        row["decision_candidate"] = {
            "proposed_by": reviewer,
            "text": business_policy_edit,
            "captured_at": now(),
            "canonical_auto_apply": False,
            "required_entrypoint": "/change",
        }
        _save(path, row)
        return {
            "status": "DECISION_REQUIRED",
            "projection_current": False,
            "canonical_mutated": False,
            "change_workflow_required": True,
        }

    if accepted:
        row["lifecycle"] = "FINAL_REVIEW" if final_review else "CURRENT"
        row["reviewed_revision"] = current_revision
        row["reviewed_content_hash"] = artifact_hash
    else:
        row["lifecycle"] = "REVIEW_REJECTED"
        row["reviewed_revision"] = None
    row["reviewer"] = reviewer
    row["reviewed_at"] = now()
    _save(path, row)
    return {
        "status": row["lifecycle"],
        "projection_current": bool(accepted),
        "canonical_mutated": False,
        "human_wording_preserved": bool(accepted and final_review),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["generated", "status", "review"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--target")
    ap.add_argument("--artifact-id")
    ap.add_argument("--artifact-path")
    ap.add_argument("--audience")
    ap.add_argument("--profile-id")
    ap.add_argument("--manual-edit-policy")
    ap.add_argument("--reviewer")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--final-review", action="store_true")
    ap.add_argument("--business-policy-edit")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "generated":
            if not all([args.target, args.artifact_id, args.artifact_path, args.audience]):
                raise ValueError("generated requires target/artifact-id/artifact-path/audience")
            result = {
                "status": "PROJECTION_GENERATED",
                "projection": register_generated(
                    root,
                    target=args.target,
                    artifact_id=args.artifact_id,
                    artifact_path=args.artifact_path,
                    audience=args.audience,
                    profile_id=args.profile_id,
                    manual_edit_policy=args.manual_edit_policy,
                ),
            }
        elif args.command == "status":
            result = {
                "status": "PROJECTION_STATUS",
                "canonical_revision": canonical_revision(root),
                "views": affected(root, args.target),
            }
        else:
            if not all([args.target, args.artifact_id, args.reviewer]):
                raise ValueError("review requires target/artifact-id/reviewer")
            result = review(
                root,
                target=args.target,
                artifact_id=args.artifact_id,
                reviewer=args.reviewer,
                accepted=args.accept,
                business_policy_edit=args.business_policy_edit,
                final_review=args.final_review,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
