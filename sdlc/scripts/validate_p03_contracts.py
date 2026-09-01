#!/usr/bin/env python3
"""Deterministic P0.3 validators for Source Discovery and Reverse Sync."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

HASH = re.compile(r"^[0-9a-f]{64}$")
CLASSES = {
    "TECHNICAL_ONLY", "FUNCTIONAL_BEHAVIOR", "BUSINESS_RULE_CANDIDATE",
    "DATA_CONTRACT", "INTERFACE_CONTRACT", "SECURITY_BEHAVIOR", "UNKNOWN",
}


def add(errors, code, msg):
    errors.append(f"{code}: {msg}")


def validate_discovery(data):
    errors = []
    root = (data or {}).get("source_discovery_result")
    if not isinstance(root, dict):
        return ["DISC-001: source_discovery_result is required"]
    meta = root.get("metadata") or {}
    for key in ("discovery_id", "source_root", "source_revision", "provider_state"):
        if not meta.get(key): add(errors, "DISC-002", f"metadata.{key} is required")
    target = root.get("target") or {}
    if not target.get("source_group_id"): add(errors, "DISC-003", "target.source_group_id is required")
    programs = set(target.get("program_ids") or [])
    if not programs: add(errors, "DISC-004", "target.program_ids is required")
    artifacts = root.get("artifacts") or []
    if not artifacts: add(errors, "DISC-005", "at least one direct artifact is required")
    for i, art in enumerate(artifacts):
        if not art.get("path"): add(errors, "DISC-006", f"artifacts[{i}].path is required")
        if not HASH.match(str(art.get("file_hash", ""))): add(errors, "DISC-007", f"artifacts[{i}].file_hash must be sha256")
        pids = set(art.get("direct_program_ids") or [])
        if not pids or not pids.issubset(programs): add(errors, "DISC-008", f"artifacts[{i}] needs valid direct_program_ids")
    for i, ev in enumerate(root.get("evidence") or []):
        if ev.get("truth") != "OBSERVED": add(errors, "DISC-009", f"evidence[{i}] source evidence must be OBSERVED")
        if not ev.get("locator"): add(errors, "DISC-010", f"evidence[{i}].locator is required")
    return errors


def validate_reverse(data):
    errors = []
    diff = (data or {}).get("source_diff_evidence")
    rs = (data or {}).get("reverse_sync_candidate")
    if not isinstance(diff, dict): return ["RS-001: source_diff_evidence is required"]
    if not isinstance(rs, dict): return ["RS-002: reverse_sync_candidate is required"]
    changed = diff.get("changed_files") or []
    if not changed: add(errors, "RS-003", "changed_files is required")
    diff_programs = set(diff.get("direct_program_ids") or [])
    for i, item in enumerate(changed):
        before, after = str(item.get("before_hash", "")), str(item.get("after_hash", ""))
        if not HASH.match(before) or not HASH.match(after): add(errors, "RS-004", f"changed_files[{i}] requires sha256 hashes")
        if before == after: add(errors, "RS-005", f"changed_files[{i}] before/after hashes must differ")
        if not set(item.get("direct_program_ids") or []).issubset(diff_programs): add(errors, "RS-006", f"changed_files[{i}] direct_program_ids mismatch")
    cls = rs.get("semantic_change_class")
    if cls not in CLASSES: add(errors, "RS-007", "semantic_change_class is invalid")
    if set(rs.get("direct_program_ids") or []) != diff_programs: add(errors, "RS-008", "reverse-sync program IDs must match diff evidence")
    if rs.get("source_revision_before") != (diff.get("metadata") or {}).get("source_revision_before"): add(errors, "RS-009", "before revision mismatch")
    if rs.get("source_revision_after") != (diff.get("metadata") or {}).get("source_revision_after"): add(errors, "RS-010", "after revision mismatch")
    if cls in {"BUSINESS_RULE_CANDIDATE", "SECURITY_BEHAVIOR", "UNKNOWN"}:
        if rs.get("protected_human_truth") is not True: add(errors, "RS-011", "high-semantic change must protect human truth")
        if rs.get("required_review") not in {"L2_OR_HUMAN", "L3_OR_HUMAN", "HUMAN"}: add(errors, "RS-012", "high-semantic change requires human-capable review")
        if rs.get("status") != "REVIEW_REQUIRED": add(errors, "RS-013", "high-semantic change status must be REVIEW_REQUIRED")
    for i, stale in enumerate(rs.get("stale_candidates") or []):
        if stale.get("state") != "STALE_CANDIDATE": add(errors, "RS-014", f"stale_candidates[{i}] must remain candidate")
        if stale.get("relation") == "requirement": add(errors, "RS-015", "requirement must not be auto stale from source diff")
    for i, review in enumerate(rs.get("review_candidates") or []):
        if review.get("state") != "REVIEW_CANDIDATE": add(errors, "RS-016", f"review_candidates[{i}] must be REVIEW_CANDIDATE")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["discovery", "reverse-sync"])
    p.add_argument("path", type=Path)
    a = p.parse_args()
    try: data = yaml.safe_load(a.path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"LOAD-001: {exc}", file=sys.stderr); return 2
    errors = validate_discovery(data) if a.kind == "discovery" else validate_reverse(data)
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print(f"OK: {a.kind} contract valid: {a.path}"); return 0

if __name__ == "__main__": raise SystemExit(main())
