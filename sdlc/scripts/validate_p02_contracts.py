#!/usr/bin/env python3
"""Deterministic validators for P0.2 review queue and canonical publish requests."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

DECISIONS = {
    "KEEP_AS_RQ",
    "MAP_TO_EXISTING_RQ_AS_FR",
    "MERGE_INTO_NEW_RQ",
    "SPLIT_TO_MULTIPLE_RQ",
    "REJECT_AS_REQUIREMENT",
    "UNRESOLVED",
}
BOUNDARY = {"OPEN", "PROVISIONAL", "CONFIRMED"}
REVIEW_STATES = {
    "READY_FOR_REVIEW",
    "NEEDS_EVIDENCE",
    "DECISION_RECORDED",
    "READY_TO_PUBLISH",
    "PUBLISHED",
    "REJECTED",
}


def nonempty(value) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def add(errors: list[str], code: str, message: str) -> None:
    errors.append(f"{code}: {message}")


def validate_review_queue(data: dict) -> list[str]:
    errors: list[str] = []
    root = (data or {}).get("requirement_review_queue")
    if not isinstance(root, dict):
        return ["RQR-001: requirement_review_queue object is required"]
    meta = root.get("metadata") or {}
    items = root.get("items") or []
    if not isinstance(items, list) or not items:
        return ["RQR-002: items must contain at least one review item"]
    if meta.get("candidate_group_count") != len(items):
        add(errors, "RQR-003", "metadata.candidate_group_count must match item count")

    review_ids: list[str] = []
    group_ids: list[str] = []
    all_source_ids: list[str] = []
    publish_count = 0

    for idx, item in enumerate(items):
        item = item or {}
        for key in (
            "review_id",
            "item_type",
            "source_group_id",
            "source_requirement_ids",
            "source_count",
            "review_state",
            "decision",
            "boundary_status",
            "decision_revision",
            "publish_allowed",
        ):
            if key not in item or item.get(key) is None or item.get(key) == "":
                add(errors, "RQR-004", f"items[{idx}].{key} is required")
        if item.get("item_type") != "RQ_GROUP_REVIEW":
            add(errors, "RQR-005", f"items[{idx}].item_type must be RQ_GROUP_REVIEW")
        review_ids.append(item.get("review_id"))
        group_ids.append(item.get("source_group_id"))
        source_ids = item.get("source_requirement_ids") or []
        if item.get("source_count") != len(source_ids):
            add(errors, "RQR-006", f"items[{idx}].source_count mismatch")
        if len(source_ids) != len(set(source_ids)):
            add(errors, "RQR-007", f"items[{idx}] source IDs must be unique")
        all_source_ids.extend(source_ids)
        decision = item.get("decision")
        boundary = item.get("boundary_status")
        state = item.get("review_state")
        if decision not in DECISIONS:
            add(errors, "RQR-008", f"items[{idx}].decision is invalid")
        if boundary not in BOUNDARY:
            add(errors, "RQR-009", f"items[{idx}].boundary_status is invalid")
        if state not in REVIEW_STATES:
            add(errors, "RQR-010", f"items[{idx}].review_state is invalid")
        rq_ids = item.get("canonical_rq_ids") or []
        fr_ids = item.get("canonical_fr_ids") or []
        if decision == "UNRESOLVED":
            if boundary != "OPEN":
                add(errors, "RQR-011", f"items[{idx}] UNRESOLVED requires OPEN boundary")
            if rq_ids or fr_ids or item.get("publish_allowed") is True:
                add(errors, "RQR-012", f"items[{idx}] unresolved item must not publish canonical IDs")
        if boundary == "CONFIRMED":
            for key in ("decision_basis", "evidence_ids", "decided_by", "decided_at"):
                if not nonempty(item.get(key)):
                    add(errors, "RQR-013", f"items[{idx}] CONFIRMED requires {key}")
            if not isinstance(item.get("decision_revision"), int) or item.get("decision_revision", 0) < 1:
                add(errors, "RQR-014", f"items[{idx}] CONFIRMED requires decision_revision >= 1")
        if item.get("publish_allowed") is True:
            publish_count += 1
            if boundary != "CONFIRMED" or decision == "UNRESOLVED":
                add(errors, "RQR-015", f"items[{idx}] publish_allowed requires confirmed non-unresolved decision")

    if len(review_ids) != len(set(review_ids)):
        add(errors, "RQR-016", "review_id must be unique")
    if len(group_ids) != len(set(group_ids)):
        add(errors, "RQR-017", "source_group_id must be unique")
    if len(all_source_ids) != len(set(all_source_ids)):
        add(errors, "RQR-018", "source requirement ID must belong to only one review group")
    if nonempty(meta.get("source_row_count")) and meta.get("source_row_count") != len(set(all_source_ids)):
        add(errors, "RQR-019", "metadata.source_row_count must match unique source ID count")
    if meta.get("canonical_publish_count", 0) != publish_count:
        add(errors, "RQR-020", "metadata.canonical_publish_count must match publish_allowed count")
    return errors


def validate_publish_request(data: dict) -> list[str]:
    errors: list[str] = []
    root = (data or {}).get("canonical_publish_request")
    if not isinstance(root, dict):
        return ["PUB-001: canonical_publish_request object is required"]
    review = root.get("review_snapshot") or {}
    publish = root.get("publish") or {}
    allocation = root.get("id_allocation") or {}
    trace = root.get("trace") or {}

    for key in (
        "review_id",
        "source_group_id",
        "source_requirement_ids",
        "source_count",
        "decision",
        "boundary_status",
        "decision_basis",
        "evidence_ids",
        "decided_by",
        "decided_at",
        "decision_revision",
        "source_revision",
    ):
        if not nonempty(review.get(key)):
            add(errors, "PUB-002", f"review_snapshot.{key} is required")
    source_ids = review.get("source_requirement_ids") or []
    if review.get("source_count") != len(source_ids):
        add(errors, "PUB-003", "review_snapshot.source_count mismatch")
    if len(source_ids) != len(set(source_ids)):
        add(errors, "PUB-004", "review_snapshot source IDs must be unique")
    decision = review.get("decision")
    if review.get("boundary_status") != "CONFIRMED":
        add(errors, "PUB-005", "publish requires CONFIRMED boundary")
    if decision not in DECISIONS or decision == "UNRESOLVED":
        add(errors, "PUB-006", "publish requires a valid non-UNRESOLVED decision")
    if not isinstance(review.get("decision_revision"), int) or review.get("decision_revision", 0) < 1:
        add(errors, "PUB-007", "decision_revision must be >= 1")

    if allocation.get("status") != "PREALLOCATED":
        add(errors, "PUB-008", "canonical IDs must be PREALLOCATED")
    rq_ids = publish.get("canonical_rq_ids") or []
    fr_ids = publish.get("canonical_fr_ids") or []
    all_ids = rq_ids + fr_ids
    if len(all_ids) != len(set(all_ids)):
        add(errors, "PUB-009", "canonical IDs must be unique within request")
    if review.get("source_group_id") in all_ids:
        add(errors, "PUB-010", "candidate source_group_id must not become a canonical ID")
    if set(all_ids) != set((allocation.get("canonical_rq_ids") or []) + (allocation.get("canonical_fr_ids") or [])):
        add(errors, "PUB-011", "publish IDs must exactly match preallocated IDs")

    if decision == "KEEP_AS_RQ" and len(rq_ids) != 1:
        add(errors, "PUB-012", "KEEP_AS_RQ requires exactly one RQ")
    elif decision == "MAP_TO_EXISTING_RQ_AS_FR" and (len(rq_ids) != 1 or len(fr_ids) < 1):
        add(errors, "PUB-013", "MAP_TO_EXISTING_RQ_AS_FR requires one RQ and 1+ FR")
    elif decision == "MERGE_INTO_NEW_RQ" and len(rq_ids) != 1:
        add(errors, "PUB-014", "MERGE_INTO_NEW_RQ requires exactly one RQ")
    elif decision == "SPLIT_TO_MULTIPLE_RQ" and len(rq_ids) < 2:
        add(errors, "PUB-015", "SPLIT_TO_MULTIPLE_RQ requires 2+ RQs")
    elif decision == "REJECT_AS_REQUIREMENT" and (rq_ids or fr_ids):
        add(errors, "PUB-016", "REJECT_AS_REQUIREMENT must not publish canonical IDs")

    if trace.get("review_id") != review.get("review_id"):
        add(errors, "PUB-017", "trace.review_id must match review snapshot")
    if trace.get("decision_revision") != review.get("decision_revision"):
        add(errors, "PUB-018", "trace.decision_revision must match review snapshot")
    if not nonempty(trace.get("evidence_ids")):
        add(errors, "PUB-019", "trace.evidence_ids is required")
    if set(trace.get("evidence_ids") or []) != set(review.get("evidence_ids") or []):
        add(errors, "PUB-020", "trace evidence must match review evidence")
    return errors


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["review-queue", "publish-request"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.path)
    except Exception as exc:
        print(f"LOAD-001: {exc}", file=sys.stderr)
        return 2
    errors = validate_review_queue(data) if args.kind == "review-queue" else validate_publish_request(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"OK: {args.kind} contract valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
