#!/usr/bin/env python3
"""Create a deterministic non-canonical INTAKE Stage Input Pack from bootstrap and one source requirement ID."""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

RELATED_KEYS = ["rq", "fr", "br", "ac", "proc", "pgm", "task", "tc"]


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def candidate_id(project_id: str, source_requirement_id: str) -> str:
    digest = hashlib.sha256(f"{project_id}\x1f{source_requirement_id}".encode("utf-8")).hexdigest()[:10].upper()
    return f"RQ-CAND-{digest}"


def build(bootstrap_doc: dict[str, Any], source_requirement_id: str, source_revision: str) -> dict[str, Any]:
    boot = (bootstrap_doc or {}).get("project_bootstrap") or {}
    project_id = boot.get("project_id")
    mode = boot.get("resolved_mode")
    profile = boot.get("artifact_profile") or "STANDARD"
    if not project_id or not mode:
        raise ValueError("bootstrap result requires project_id and resolved_mode")
    cid = candidate_id(str(project_id), source_requirement_id)
    return {
        "version": 1.3,
        "stage_input_pack": {
            "metadata": {
                "pack_id": f"PACK-{cid}-INTAKE",
                "project_id": project_id,
                "project_mode": mode,
                "stage": "INTAKE",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_revision": source_revision,
                "profile": profile,
                "granularity": "ROW",
                "source_group_id": None,
            },
            "target": {
                "primary_id": cid,
                "target_type": "RQ_CANDIDATE",
                "boundary_status": "OPEN",
                "source_requirement_ids": [source_requirement_id],
                "related_ids": {key: [] for key in RELATED_KEYS},
            },
            "required_inputs": [{"type": "SOURCE_REQUIREMENT", "id": source_requirement_id}],
            "resolved_facts": [],
            "evidence": [],
            "open_items": list(boot.get("open_items") or []),
            "constraints": {
                "do_not_invent_missing_business_fact": True,
                "source_behavior_is_not_business_truth": True,
                "ambiguous_write_must_not_be_auto_selected": True,
            },
            "execution": {
                "requested_actions": [],
                "requested_outputs": [],
                "capability_inputs": {},
                "write_proofs": {},
                "human_actions": [],
                "adapter_configs": {},
            },
            "expected_outputs": ["requirement_customer_view", "stage_input_pack"],
            "next_actions": ["REVIEW_REQUIREMENT_BOUNDARY", "RESOLVE_ONLY_NEEDED_OPEN_ITEMS"],
            "validation": {
                "required_field_check": "PENDING",
                "id_reference_check": "PENDING",
                "open_preservation_check": "PENDING",
                "boundary_guard_check": "PENDING",
                "granularity_check": "PENDING",
                "execution_scope_check": "PENDING",
                "artifact_profile_check": "PENDING",
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bootstrap", type=Path)
    parser.add_argument("source_requirement_id")
    parser.add_argument("source_revision")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = build(load(args.bootstrap), args.source_requirement_id, args.source_revision)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
