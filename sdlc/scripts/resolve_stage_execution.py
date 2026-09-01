#!/usr/bin/env python3
"""Resolve one Stage Input Pack into deterministic skill/capability/output instructions."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def action_blockers(open_items: list[dict[str, Any]], action: str) -> list[dict[str, Any]]:
    blocked = []
    for item in open_items:
        if item.get("blocks_action") is not True:
            continue
        scopes = item.get("action_scopes") or item.get("action_scope") or ["*"]
        if isinstance(scopes, str):
            scopes = [scopes]
        if "*" in scopes or action in scopes:
            blocked.append(item)
    return blocked


def resolve(routing: dict[str, Any], pack_doc: dict[str, Any], artifact_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    pack = (pack_doc or {}).get("stage_input_pack") or {}
    metadata = pack.get("metadata") or {}
    stage = metadata.get("stage")
    mode = metadata.get("project_mode") or "AUTO"
    stage_cfg = ((routing.get("stages") or {}).get(stage))
    if not stage_cfg:
        raise ValueError(f"stage is not routable: {stage}")

    mode_cfg = ((stage_cfg.get("mode_rules") or {}).get(mode)) or {}
    required = list(mode_cfg.get("required_capabilities", stage_cfg.get("required_capabilities") or []))
    optional = list(mode_cfg.get("optional_capabilities", stage_cfg.get("optional_capabilities") or []))
    capabilities = unique(required + optional)

    outputs = list(stage_cfg.get("output_artifacts") or [])
    if artifact_plan:
        human = artifact_plan.get("human_artifacts") or {}
        filtered = []
        suppressed = []
        for output in outputs:
            rule = human.get(output)
            if rule in {"OFF", "DISABLED", False}:
                suppressed.append(output)
            else:
                filtered.append(output)
        outputs = filtered
    else:
        suppressed = []

    open_items = list(pack.get("open_items") or [])
    reasoning_blockers = [item for item in open_items if item.get("blocks_reasoning") is True]
    actions = []
    for action in stage_cfg.get("side_effect_actions") or []:
        blockers = action_blockers(open_items, action)
        actions.append({
            "action": action,
            "state": "GUARDED" if blockers else "READY_FOR_PROOF_CHECK",
            "blocker_ids": [b.get("open_id") for b in blockers if b.get("open_id")],
        })

    return {
        "schema_version": 1,
        "artifact_type": "STAGE_EXECUTION_PLAN",
        "stage_execution": {
            "pack_id": metadata.get("pack_id"),
            "project_id": metadata.get("project_id"),
            "project_mode": mode,
            "profile": metadata.get("profile"),
            "stage": stage,
            "skill": stage_cfg.get("skill"),
            "required_capabilities": required,
            "optional_capabilities": optional,
            "requested_capabilities": capabilities,
            "expected_outputs": outputs,
            "suppressed_human_outputs": suppressed,
            "next_stage": stage_cfg.get("next_stage"),
            "read_only_progress_allowed": not reasoning_blockers,
            "reasoning_blocker_ids": [b.get("open_id") for b in reasoning_blockers if b.get("open_id")],
            "side_effect_actions": actions,
            "nonblocking_open_ids": [
                item.get("open_id") for item in open_items
                if not item.get("blocks_reasoning") and not item.get("blocks_action") and item.get("open_id")
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("routing", type=Path)
    parser.add_argument("stage_pack", type=Path)
    parser.add_argument("--artifact-plan", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    artifact_plan = load(args.artifact_plan) if args.artifact_plan else None
    result = resolve(load(args.routing), load(args.stage_pack), artifact_plan)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
