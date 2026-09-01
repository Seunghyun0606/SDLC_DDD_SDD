#!/usr/bin/env python3
"""Deterministic P0/P0.1 validators for legacy normalization, boundary, and Stage Input Pack."""

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
BOUNDARY_SCOPE = {"ROW", "GROUP", "SUBGROUP"}
PACK_GRANULARITY = {"ROW", "GROUP", "SUBGROUP", "CANONICAL_ENTITY"}
NORMALIZER_STRATEGIES = {"EXACT_LEVEL2_REQUIREMENT_NAME"}
PARTITION_MODES = {"ALL_ROWS_EXACTLY_ONCE", "PARTIAL_REVIEW"}
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
        source_ids = []
    elif len(source_ids) != len(set(source_ids)):
        add(errors, "SIP-021", "target.source_requirement_ids must be unique")

    related = target.get("related_ids")
    if not isinstance(related, dict) or not RELATED_KEYS.issubset(set(related)):
        add(errors, "SIP-006", f"target.related_ids must contain {sorted(RELATED_KEYS)}")

    granularity = meta.get("granularity")
    group_id = meta.get("source_group_id")
    if len(source_ids) > 1:
        if granularity not in {"GROUP", "SUBGROUP"}:
            add(errors, "SIP-022", "multi-row legacy handoff requires metadata.granularity GROUP or SUBGROUP")
        if not nonempty(group_id):
            add(errors, "SIP-023", "multi-row legacy handoff requires metadata.source_group_id")
    elif granularity is not None and granularity not in PACK_GRANULARITY:
        add(errors, "SIP-024", f"metadata.granularity must be one of {sorted(PACK_GRANULARITY)}")
    if granularity in {"GROUP", "SUBGROUP"} and not nonempty(group_id):
        add(errors, "SIP-025", "GROUP/SUBGROUP pack requires metadata.source_group_id")
    if granularity == "ROW" and len(source_ids) != 1:
        add(errors, "SIP-026", "ROW granularity requires exactly one source requirement ID")

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


def _boundary_source_ids(rec):
    if isinstance(rec.get("source_requirement_ids"), list):
        return rec.get("source_requirement_ids") or []
    if nonempty(rec.get("source_requirement_id")):
        return [rec.get("source_requirement_id")]
    return []


def validate_boundary(data):
    errors = []
    records = (data or {}).get("boundary_records")
    if not isinstance(records, list) or not records:
        return ["RQB-001: boundary_records must contain at least one record"]

    all_source_ids = []
    for idx, rec in enumerate(records):
        rec = rec or {}
        source_ids = _boundary_source_ids(rec)
        if not source_ids:
            add(errors, "RQB-002", f"boundary_records[{idx}] must preserve source requirement ID(s)")
        if len(source_ids) != len(set(source_ids)):
            add(errors, "RQB-013", f"boundary_records[{idx}].source_requirement_ids must be unique")
        all_source_ids.extend(source_ids)

        scope = rec.get("scope_type")
        if scope is None:
            scope = "ROW" if len(source_ids) <= 1 else None
        if scope not in BOUNDARY_SCOPE:
            add(errors, "RQB-014", f"boundary_records[{idx}].scope_type must be one of {sorted(BOUNDARY_SCOPE)}")
        if len(source_ids) > 1:
            if scope not in {"GROUP", "SUBGROUP"}:
                add(errors, "RQB-015", f"boundary_records[{idx}] multi-row boundary must use GROUP or SUBGROUP scope")
            if not nonempty(rec.get("source_group_id")):
                add(errors, "RQB-016", f"boundary_records[{idx}] multi-row boundary requires source_group_id")
        if nonempty(rec.get("source_count")) and rec.get("source_count") != len(source_ids):
            add(errors, "RQB-017", f"boundary_records[{idx}].source_count must equal number of source IDs")

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

    if len(all_source_ids) != len(set(all_source_ids)):
        add(errors, "RQB-012", "source requirement IDs must not appear in multiple boundary records")
    return errors


def validate_normalization(data):
    errors = []
    root = (data or {}).get("legacy_requirement_normalization")
    if not isinstance(root, dict):
        return ["LRN-001: legacy_requirement_normalization object is required"]

    meta = root.get("metadata") or {}
    for key in ("normalizer_id", "source_name", "source_revision", "strategy", "partition_mode"):
        if not nonempty(meta.get(key)):
            add(errors, "LRN-002", f"metadata.{key} is required")
    strategy = meta.get("strategy")
    partition_mode = meta.get("partition_mode")
    if strategy not in NORMALIZER_STRATEGIES:
        add(errors, "LRN-003", f"metadata.strategy must be one of {sorted(NORMALIZER_STRATEGIES)}")
    if partition_mode not in PARTITION_MODES:
        add(errors, "LRN-004", f"metadata.partition_mode must be one of {sorted(PARTITION_MODES)}")

    rows = root.get("source_rows")
    if not isinstance(rows, list) or not rows:
        return errors + ["LRN-005: source_rows must contain at least one row"]
    row_map = {}
    for idx, row in enumerate(rows):
        row = row or {}
        sid = row.get("source_requirement_id")
        if not nonempty(sid):
            add(errors, "LRN-006", f"source_rows[{idx}].source_requirement_id is required")
            continue
        if sid in row_map:
            add(errors, "LRN-007", f"duplicate source_requirement_id: {sid}")
        row_map[sid] = row
        for key in ("level2", "requirement_name"):
            if not nonempty(row.get(key)):
                add(errors, "LRN-008", f"source_rows[{idx}].{key} is required for exact grouping")

    groups = root.get("candidate_groups")
    if not isinstance(groups, list) or not groups:
        return errors + ["LRN-009: candidate_groups must contain at least one group"]

    group_ids = set()
    assigned = []
    for idx, group in enumerate(groups):
        group = group or {}
        gid = group.get("group_id")
        if not nonempty(gid):
            add(errors, "LRN-010", f"candidate_groups[{idx}].group_id is required")
        elif gid in group_ids:
            add(errors, "LRN-011", f"duplicate group_id: {gid}")
        else:
            group_ids.add(gid)

        source_ids = group.get("source_requirement_ids")
        if not isinstance(source_ids, list) or not source_ids:
            add(errors, "LRN-012", f"candidate_groups[{idx}].source_requirement_ids must not be empty")
            source_ids = []
        if len(source_ids) != len(set(source_ids)):
            add(errors, "LRN-013", f"candidate_groups[{idx}] contains duplicate source IDs")
        assigned.extend(source_ids)

        unknown = [sid for sid in source_ids if sid not in row_map]
        if unknown:
            add(errors, "LRN-014", f"candidate_groups[{idx}] references unknown source IDs {unknown}")

        if group.get("publish_canonical") is not False:
            add(errors, "LRN-015", f"candidate_groups[{idx}].publish_canonical must be false")
        if group.get("boundary_status") != "OPEN":
            add(errors, "LRN-016", f"candidate_groups[{idx}].boundary_status must be OPEN")
        if group.get("canonical_decision") != "UNRESOLVED":
            add(errors, "LRN-017", f"candidate_groups[{idx}].canonical_decision must be UNRESOLVED")

        key = group.get("grouping_key") or {}
        if strategy == "EXACT_LEVEL2_REQUIREMENT_NAME":
            if set(key) != {"level2", "requirement_name"}:
                add(errors, "LRN-018", f"candidate_groups[{idx}].grouping_key must contain exactly level2 and requirement_name")
            for sid in source_ids:
                row = row_map.get(sid)
                if not row:
                    continue
                if row.get("level2") != key.get("level2") or row.get("requirement_name") != key.get("requirement_name"):
                    add(errors, "LRN-019", f"candidate_groups[{idx}] violates exact grouping for source ID {sid}")

        if nonempty(group.get("source_count")) and group.get("source_count") != len(source_ids):
            add(errors, "LRN-020", f"candidate_groups[{idx}].source_count must equal number of source IDs")

    if len(assigned) != len(set(assigned)):
        add(errors, "LRN-021", "a source requirement ID must not belong to multiple exact candidate groups")
    if partition_mode == "ALL_ROWS_EXACTLY_ONCE":
        if set(assigned) != set(row_map):
            missing = sorted(set(row_map) - set(assigned))
            extra = sorted(set(assigned) - set(row_map))
            add(errors, "LRN-022", f"partition must cover every source row exactly once; missing={missing}, extra={extra}")

    subgroups = root.get("subgroup_candidates") or []
    for idx, subgroup in enumerate(subgroups):
        subgroup = subgroup or {}
        if subgroup.get("truth") != "INFERRED":
            add(errors, "LRN-023", f"subgroup_candidates[{idx}].truth must be INFERRED")
        if subgroup.get("publish_canonical") is not False:
            add(errors, "LRN-024", f"subgroup_candidates[{idx}].publish_canonical must be false")
        parent = subgroup.get("parent_group_id")
        if parent not in group_ids:
            add(errors, "LRN-025", f"subgroup_candidates[{idx}] parent_group_id must reference a candidate group")
        sids = subgroup.get("source_requirement_ids") or []
        unknown = [sid for sid in sids if sid not in row_map]
        if unknown:
            add(errors, "LRN-026", f"subgroup_candidates[{idx}] references unknown source IDs {unknown}")

    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["stage-pack", "rq-boundary", "legacy-normalization"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        data = load_yaml(args.path)
    except Exception as exc:
        print(f"LOAD-001: {exc}", file=sys.stderr)
        return 2

    validators = {
        "stage-pack": validate_stage_pack,
        "rq-boundary": validate_boundary,
        "legacy-normalization": validate_normalization,
    }
    errors = validators[args.kind](data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"OK: {args.kind} contract valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
