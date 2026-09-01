#!/usr/bin/env python3
"""Deterministic P0 validators for Stage Input Pack and Requirement Boundary files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

TRUTH = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
PROFILES = {"LITE", "STANDARD", "ENTERPRISE"}
BOUNDARY_DECISIONS = {
    "KEEP_AS_RQ",
    "MAP_TO_EXISTING_RQ_AS_FR",
    "MERGE_INTO_NEW_RQ",
    "SPLIT_TO_MULTIPLE_RQ",
    "UNRESOLVED",
}
BOUNDARY_STATUS = {"CONFIRMED", "PROVISIONAL", "OPEN"}
RELATED_KEYS = {"rq", "fr", "br", "ac", "proc", "pgm", "task", "tc"}


def load_yaml(path: Path):
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def nonempty(value) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def add(errors, code, message):
    errors.append(f"{code}: {message}")


def validate_stage_pack(data):
    errors = []
    root = (data or {}).get("stage_input_pack")
    if not isinstance(root, dict):
        return ["SIP-001: stage_input_pack object is required"]

    meta = root.get("metadata") or {}
    for key in ("pack_id", "project_id", "stage", "source_revision", "profile"):
        if not nonempty(meta.get(key)):
            add(errors, "SIP-002", f"metadata.{key} is required")
    if meta.get("profile") not in PROFILES:
        add(errors, "SIP-003", f"metadata.profile must be one of {sorted(PROFILES)}")

    target = root.get("target") or {}
    for key in ("primary_id", "target_type", "boundary_status"):
        if not nonempty(target.get(key)):
            add(errors, "SIP-004", f"target.{key} is required")
    source_ids = target.get("source_requirement_ids")
    if not isinstance(source_ids, list) or not source_ids:
        add(errors, "SIP-005", "target.source_requirement_ids must preserve at least one source ID")
    related = target.get("related_ids")
    if not isinstance(related, dict) or not RELATED_KEYS.issubset(set(related)):
        add(errors, "SIP-006", f"target.related_ids must contain {sorted(RELATED_KEYS)}")

    evidence = root.get("evidence") or []
    evidence_ids = []
    for idx, item in enumerate(evidence):
        eid = (item or {}).get("evidence_id")
        if not nonempty(eid):
            add(errors, "SIP-007", f"evidence[{idx}].evidence_id is required")
        else:
            evidence_ids.append(eid)
    if len(evidence_ids) != len(set(evidence_ids)):
        add(errors, "SIP-008", "evidence_id must be unique")
    evidence_set = set(evidence_ids)

    fact_ids = []
    for idx, fact in enumerate(root.get("resolved_facts") or []):
        fact = fact or {}
        fid = fact.get("fact_id")
        if not nonempty(fid):
            add(errors, "SIP-009", f"resolved_facts[{idx}].fact_id is required")
        else:
            fact_ids.append(fid)
        truth = fact.get("truth")
        if truth not in TRUTH:
            add(errors, "SIP-010", f"resolved_facts[{idx}].truth must be one of {sorted(TRUTH)}")
        refs = fact.get("evidence_ids") or []
        missing = [ref for ref in refs if ref not in evidence_set]
        if missing:
            add(errors, "SIP-011", f"resolved_facts[{idx}] references missing evidence {missing}")
        if truth == "CONFIRMED" and not refs:
            add(errors, "SIP-012", f"resolved_facts[{idx}] CONFIRMED requires evidence")
    if len(fact_ids) != len(set(fact_ids)):
        add(errors, "SIP-013", "fact_id must be unique")

    open_ids = []
    open_items = root.get("open_items") or []
    for idx, item in enumerate(open_items):
        item = item or {}
        oid = item.get("open_id")
        if not nonempty(oid):
            add(errors, "SIP-014", f"open_items[{idx}].open_id is required")
        else:
            open_ids.append(oid)
        for key in ("type", "question", "blocks_reasoning", "blocks_action", "escalation"):
            if key not in item or item.get(key) is None or item.get(key) == "":
                add(errors, "SIP-015", f"open_items[{idx}].{key} is required")
        if item.get("blocks_reasoning") is True and not nonempty(item.get("required_evidence")):
            add(errors, "SIP-016", f"open_items[{idx}] reasoning blocker requires required_evidence")
    if len(open_ids) != len(set(open_ids)):
        add(errors, "SIP-017", "open_id must be unique")

    ambiguous = any((item or {}).get("type") == "BOUNDARY_AMBIGUOUS" for item in open_items)
    if ambiguous:
        if target.get("boundary_status") != "OPEN":
            add(errors, "SIP-018", "BOUNDARY_AMBIGUOUS requires target.boundary_status=OPEN")
        if not str(target.get("target_type", "")).endswith("CANDIDATE"):
            add(errors, "SIP-019", "BOUNDARY_AMBIGUOUS target must remain a candidate")

    constraints = root.get("constraints") or {}
    for key in (
        "do_not_invent_missing_business_fact",
        "source_behavior_is_not_business_truth",
        "ambiguous_write_must_not_be_auto_selected",
    ):
        if constraints.get(key) is not True:
            add(errors, "SIP-020", f"constraints.{key} must be true")

    return errors


def validate_boundary(data):
    errors = []
    records = (data or {}).get("boundary_records")
    if not isinstance(records, list) or not records:
        return ["RQB-001: boundary_records must contain at least one record"]

    source_ids = []
    for idx, rec in enumerate(records):
        rec = rec or {}
        sid = rec.get("source_requirement_id")
        if not nonempty(sid):
            add(errors, "RQB-002", f"boundary_records[{idx}].source_requirement_id is required")
        else:
            source_ids.append(sid)
        decision = rec.get("decision")
        status = rec.get("status")
        rq_ids = rec.get("canonical_rq_ids") or []
        fr_ids = rec.get("canonical_fr_ids") or []
        if decision not in BOUNDARY_DECISIONS:
            add(errors, "RQB-003", f"boundary_records[{idx}].decision is invalid")
            continue
        if status not in BOUNDARY_STATUS:
            add(errors, "RQB-004", f"boundary_records[{idx}].status is invalid")
        if decision == "UNRESOLVED":
            if rq_ids or fr_ids:
                add(errors, "RQB-005", f"boundary_records[{idx}] UNRESOLVED must not publish canonical IDs")
            if not nonempty(rec.get("escalation")):
                add(errors, "RQB-006", f"boundary_records[{idx}] UNRESOLVED requires escalation")
        elif decision == "KEEP_AS_RQ":
            if len(rq_ids) != 1:
                add(errors, "RQB-007", f"boundary_records[{idx}] KEEP_AS_RQ requires exactly one RQ")
        elif decision == "MAP_TO_EXISTING_RQ_AS_FR":
            if len(rq_ids) != 1 or len(fr_ids) < 1:
                add(errors, "RQB-008", f"boundary_records[{idx}] MAP_TO_EXISTING_RQ_AS_FR requires one RQ and at least one FR")
        elif decision == "MERGE_INTO_NEW_RQ":
            if len(rq_ids) != 1 or not nonempty(rec.get("evidence_ids")):
                add(errors, "RQB-009", f"boundary_records[{idx}] MERGE_INTO_NEW_RQ requires one RQ and evidence")
        elif decision == "SPLIT_TO_MULTIPLE_RQ":
            if len(rq_ids) < 2 or not nonempty(rec.get("evidence_ids")):
                add(errors, "RQB-010", f"boundary_records[{idx}] SPLIT_TO_MULTIPLE_RQ requires 2+ RQs and evidence")
            if status == "CONFIRMED" and not nonempty(rec.get("decided_by")):
                add(errors, "RQB-011", f"boundary_records[{idx}] confirmed split requires decided_by")

    if len(source_ids) != len(set(source_ids)):
        add(errors, "RQB-012", "source_requirement_id must be unique")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["stage-pack", "rq-boundary"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        data = load_yaml(args.path)
    except Exception as exc:
        print(f"LOAD-001: {exc}", file=sys.stderr)
        return 2

    errors = validate_stage_pack(data) if args.kind == "stage-pack" else validate_boundary(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"OK: {args.kind} contract valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
