#!/usr/bin/env python3
"""Deterministic Legacy Requirement Normalizer (P0.1).

Input is an extraction-layer YAML file, not a workbook. This keeps document parsing
separate from canonical boundary decisions.
"""

from __future__ import annotations

import argparse
import hashlib
from collections import OrderedDict
from pathlib import Path

import yaml


def stable_group_id(level2: str, requirement_name: str) -> str:
    raw = f"{level2}\x1f{requirement_name}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:10].upper()
    return f"RQG-CAND-{digest}"


def group_rows(payload: dict) -> dict:
    source = payload.get("source") or {}
    rows = payload.get("rows") or []
    if not rows:
        raise ValueError("rows must contain at least one source row")

    seen = set()
    groups = OrderedDict()
    normalized_rows = []

    for index, row in enumerate(rows):
        row = row or {}
        sid = row.get("source_requirement_id")
        level2 = row.get("level2")
        requirement_name = row.get("requirement_name")
        if not sid:
            raise ValueError(f"rows[{index}].source_requirement_id is required")
        if sid in seen:
            raise ValueError(f"duplicate source_requirement_id: {sid}")
        if not level2 or not requirement_name:
            raise ValueError(f"rows[{index}] requires level2 and requirement_name")
        seen.add(sid)

        normalized = {
            "source_requirement_id": sid,
            "level1": row.get("level1"),
            "level2": level2,
            "requirement_name": requirement_name,
        }
        if row.get("functional_item") is not None:
            normalized["functional_item"] = row.get("functional_item")
        normalized_rows.append(normalized)

        key = (level2, requirement_name)
        groups.setdefault(key, []).append(sid)

    candidate_groups = []
    for (level2, requirement_name), source_ids in groups.items():
        candidate_groups.append(
            {
                "group_id": stable_group_id(level2, requirement_name),
                "grouping_key": {
                    "level2": level2,
                    "requirement_name": requirement_name,
                },
                "source_requirement_ids": source_ids,
                "source_count": len(source_ids),
                "boundary_status": "OPEN",
                "canonical_decision": "UNRESOLVED",
                "publish_canonical": False,
            }
        )

    return {
        "version": 1,
        "legacy_requirement_normalization": {
            "metadata": {
                "normalizer_id": source.get("normalizer_id") or "LRN-AUTO-001",
                "source_name": source.get("name") or "UNKNOWN_SOURCE",
                "source_revision": source.get("revision") or "OPEN",
                "strategy": "EXACT_LEVEL2_REQUIREMENT_NAME",
                "partition_mode": "ALL_ROWS_EXACTLY_ONCE",
                "group_id_strategy": "SHA256_EXACT_KEY_10",
            },
            "source_rows": normalized_rows,
            "candidate_groups": candidate_groups,
            "subgroup_candidates": [],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}
    result = group_rows(payload)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
