#!/usr/bin/env python3
"""Build a 12-stage /check read model from Stage Input Pack v2 artifacts without creating truth."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def classify_pack(pack):
    root = (pack or {}).get("stage_input_pack") or {}
    open_items = root.get("open_items") or []
    outputs = [item for item in (root.get("expected_outputs") or []) if item.get("required") is not False]
    blocking = [item for item in open_items if item.get("blocks_action") is True]
    if blocking:
        return "ACTION_REQUIRED"
    states = {item.get("state") for item in outputs}
    if outputs and states == {"COMPLETE"}:
        return "COMPLETE_WITH_OPEN" if open_items else "COMPLETE"
    if "PARTIAL" in states or "OPEN" in states or "PLANNED" in states or not outputs:
        return "PARTIAL"
    return "PARTIAL"


def build_status(routing, pack_docs):
    order = routing.get("stage_order") or []
    stage_rules = routing.get("stages") or {}
    packs = {}
    duplicates = []
    for pack in pack_docs:
        root = (pack or {}).get("stage_input_pack") or {}
        stage = (root.get("metadata") or {}).get("stage")
        if not stage:
            continue
        if stage in packs:
            duplicates.append(stage)
        packs[stage] = pack

    if duplicates:
        return None, [f"STATUS-001: multiple Stage Input Packs for stage(s): {sorted(set(duplicates))}"]

    stage_status = []
    first_incomplete = None
    last_present_index = -1
    for index, stage in enumerate(order):
        rule = stage_rules.get(stage) or {}
        pack = packs.get(stage)
        if pack is None:
            state = "NOT_STARTED"
            output_summary = []
            open_count = 0
        else:
            last_present_index = max(last_present_index, index)
            state = classify_pack(pack)
            root = pack.get("stage_input_pack") or {}
            output_summary = [
                {"output_type": item.get("output_type"), "state": item.get("state")}
                for item in (root.get("expected_outputs") or [])
            ]
            open_count = len(root.get("open_items") or [])
        if first_incomplete is None and state not in {"COMPLETE", "COMPLETE_WITH_OPEN"}:
            first_incomplete = stage
        stage_status.append({
            "stage": stage,
            "display_name_ko": rule.get("display_name_ko"),
            "state": state,
            "skill": rule.get("skill"),
            "procedure_profile": rule.get("procedure_profile"),
            "expected_outputs": output_summary,
            "open_count": open_count,
        })

    if first_incomplete is None and order:
        current_stage = order[-1]
    elif first_incomplete is not None:
        current_stage = first_incomplete
    elif last_present_index >= 0:
        current_stage = order[min(last_present_index + 1, len(order) - 1)]
    else:
        current_stage = order[0] if order else None

    current_pack = packs.get(current_stage)
    current_root = (current_pack or {}).get("stage_input_pack") or {}
    next_actions = list(current_root.get("next_actions") or [])
    current_rule = stage_rules.get(current_stage) or {}
    if not next_actions and current_stage:
        next_actions = [{
            "action_type": "CONTINUE_STAGE",
            "description_ko": f"{current_rule.get('display_name_ko') or current_stage} 단계를 진행한다.",
            "side_effect": False,
        }]

    any_action_required = any(item["state"] == "ACTION_REQUIRED" for item in stage_status)
    all_complete = bool(stage_status) and all(item["state"] in {"COMPLETE", "COMPLETE_WITH_OPEN"} for item in stage_status)
    if all_complete:
        overall = "COMPLETE"
    elif any_action_required:
        overall = "ACTION_REQUIRED"
    else:
        overall = "IN_PROGRESS"

    result = {
        "version": 1,
        "sdlc_status_view": {
            "overall_state": overall,
            "current_stage": current_stage,
            "stage_status": stage_status,
            "next_actions": next_actions[:5],
            "truth_guards": {
                "read_model_creates_truth": False,
                "candidate_is_not_canonical": True,
                "provider_partial_is_preserved": True,
                "runtime_not_executed_is_not_pass": True,
            },
        },
    }
    return result, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("routing", type=Path)
    parser.add_argument("stage_packs", type=Path, nargs="*")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result, errors = build_status(load(args.routing), [load(path) for path in args.stage_packs])
    except Exception as exc:
        print(f"STATUS-LOAD: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: SDLC status view built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
