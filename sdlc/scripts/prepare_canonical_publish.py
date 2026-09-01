#!/usr/bin/env python3
"""Prepare a canonical publish request from a CONFIRMED review decision.

This script does not allocate IDs and does not write Canonical registries.
Canonical IDs must be preallocated and supplied explicitly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def nonempty(value) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def prepare(review_payload: dict, rq_ids: list[str], fr_ids: list[str]) -> dict:
    review = (review_payload or {}).get("requirement_review_decision")
    if not isinstance(review, dict):
        raise ValueError("requirement_review_decision object is required")
    if review.get("boundary_status") != "CONFIRMED":
        raise ValueError("boundary_status must be CONFIRMED")
    decision = review.get("decision")
    if decision in (None, "", "UNRESOLVED"):
        raise ValueError("confirmed non-UNRESOLVED decision is required")
    for key in ("review_id", "source_group_id", "source_revision", "source_requirement_ids", "decision_basis", "evidence_ids", "decided_by", "decided_at", "decision_revision"):
        if not nonempty(review.get(key)):
            raise ValueError(f"{key} is required")
    source_ids = review.get("source_requirement_ids") or []
    if review.get("source_count") != len(source_ids):
        raise ValueError("source_count mismatch")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_requirement_ids must be unique")
    if review.get("source_group_id") in set(rq_ids + fr_ids):
        raise ValueError("candidate group ID cannot be used as canonical ID")

    return {
        "version": 1,
        "canonical_publish_request": {
            "review_snapshot": {
                "review_id": review["review_id"],
                "source_group_id": review["source_group_id"],
                "source_requirement_ids": source_ids,
                "source_count": review["source_count"],
                "decision": decision,
                "boundary_status": review["boundary_status"],
                "decision_basis": review["decision_basis"],
                "evidence_ids": review["evidence_ids"],
                "decided_by": review["decided_by"],
                "decided_at": review["decided_at"],
                "decision_revision": review["decision_revision"],
                "source_revision": review["source_revision"],
            },
            "id_allocation": {
                "status": "PREALLOCATED",
                "canonical_rq_ids": rq_ids,
                "canonical_fr_ids": fr_ids,
            },
            "publish": {
                "canonical_rq_ids": rq_ids,
                "canonical_fr_ids": fr_ids,
            },
            "trace": {
                "review_id": review["review_id"],
                "decision_revision": review["decision_revision"],
                "evidence_ids": review["evidence_ids"],
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("review", type=Path)
    parser.add_argument("--rq", action="append", default=[])
    parser.add_argument("--fr", action="append", default=[])
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    payload = yaml.safe_load(args.review.read_text(encoding="utf-8")) or {}
    result = prepare(payload, args.rq, args.fr)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
