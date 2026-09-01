#!/usr/bin/env python3
"""Build a deterministic P0.2 requirement boundary review queue.

Inputs:
- P0 pilot candidate groups with full source IDs
- P0.1 stable ID crosswalk

The output is a review queue, not Canonical RQ/FR publication.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def priority(level2: str, source_count: int) -> tuple[str, str]:
    if source_count >= 20 or level2 in {"Batch", "Interface"}:
        return "HIGH", "HEURISTIC_ONLY"
    if source_count >= 5:
        return "MEDIUM", "HEURISTIC_ONLY"
    return "LOW", "HEURISTIC_ONLY"


def build(groups_payload: dict, crosswalk_payload: dict) -> dict:
    groups = groups_payload.get("candidate_groups") or []
    crosswalk = crosswalk_payload.get("crosswalk") or []
    stable_by_legacy = {
        item["legacy_pilot_group_id"]: item["stable_group_id"]
        for item in crosswalk
    }
    items = []
    seen_source_ids = set()

    for group in groups:
        legacy_id = group["candidate_group_id"]
        stable_id = stable_by_legacy.get(legacy_id)
        if not stable_id:
            raise ValueError(f"stable ID missing for {legacy_id}")
        source_ids = list(group.get("source_ids") or [])
        if group.get("source_count") != len(source_ids):
            raise ValueError(f"source_count mismatch for {legacy_id}")
        duplicate = [sid for sid in source_ids if sid in seen_source_ids]
        if duplicate:
            raise ValueError(f"source IDs assigned to multiple groups: {duplicate}")
        seen_source_ids.update(source_ids)
        p, truth = priority(group.get("level2") or "", len(source_ids))
        items.append(
            {
                "review_id": f"RQR-{stable_id.removeprefix('RQG-CAND-')}",
                "item_type": "RQ_GROUP_REVIEW",
                "source_group_id": stable_id,
                "legacy_pilot_group_id": legacy_id,
                "level1": group.get("level1"),
                "level2": group.get("level2"),
                "requirement_name": group.get("requirement_name"),
                "source_requirement_ids": source_ids,
                "source_count": len(source_ids),
                "review_priority": p,
                "priority_truth": truth,
                "review_state": "READY_FOR_REVIEW",
                "decision": "UNRESOLVED",
                "boundary_status": "OPEN",
                "canonical_rq_ids": [],
                "canonical_fr_ids": [],
                "decision_basis": "OPEN",
                "evidence_ids": [],
                "decided_by": None,
                "decided_at": None,
                "decision_revision": 0,
                "required_evidence": [
                    "business_outcome_boundary",
                    "owner_release_acceptance_boundary",
                ],
                "publish_allowed": False,
            }
        )

    items.sort(key=lambda x: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["review_priority"]], -x["source_count"], x["source_group_id"]))
    return {
        "version": 1,
        "requirement_review_queue": {
            "metadata": {
                "source": groups_payload.get("source", {}).get("file", "요구사항목록.xlsx"),
                "candidate_group_count": len(items),
                "source_row_count": len(seen_source_ids),
                "projection": "RQ_GROUP_REVIEW",
                "canonical_publish_count": 0,
            },
            "items": items,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("groups", type=Path)
    parser.add_argument("crosswalk", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    groups_payload = yaml.safe_load(args.groups.read_text(encoding="utf-8")) or {}
    crosswalk_payload = yaml.safe_load(args.crosswalk.read_text(encoding="utf-8")) or {}
    result = build(groups_payload, crosswalk_payload)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
