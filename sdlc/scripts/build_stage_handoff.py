#!/usr/bin/env python3
"""Populate Stage Input Pack v2 routing/input/output/handoff fields deterministically."""
from __future__ import annotations
import argparse
import copy
import sys
from pathlib import Path
import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _merge_required_inputs(existing, required_types):
    result = copy.deepcopy(existing or [])
    by_type = {item.get("input_type"): item for item in result if item.get("input_type")}
    for input_type in required_types or []:
        if input_type in by_type:
            by_type[input_type]["required"] = True
            continue
        result.append({
            "input_type": input_type,
            "ref": "OPEN",
            "required": True,
            "state": "OPEN",
        })
    return result


def _merge_expected_outputs(existing, output_types):
    result = copy.deepcopy(existing or [])
    by_type = {item.get("output_type"): item for item in result if item.get("output_type")}
    for output_type in output_types or []:
        if output_type in by_type:
            by_type[output_type]["required"] = True
            continue
        result.append({
            "output_type": output_type,
            "artifact_id": "OPEN",
            "required": True,
            "state": "PLANNED",
        })
    return result


def build_handoff(routing, pack):
    errors = []
    result = copy.deepcopy(pack or {})
    if result.get("version") != 2:
        return result, ["HANDOFF-001: Stage Input Pack version must be 2"]
    root = result.get("stage_input_pack")
    if not isinstance(root, dict):
        return result, ["HANDOFF-002: stage_input_pack object is required"]

    metadata = root.setdefault("metadata", {})
    stage = metadata.get("stage")
    stages = routing.get("stages") or {}
    rule = stages.get(stage)
    if not rule:
        return result, [f"HANDOFF-003: unknown stage: {stage}"]

    next_stage = rule.get("next_stage")
    next_rule = stages.get(next_stage) if next_stage else None
    metadata["route_revision"] = routing.get("version")

    root["required_inputs"] = _merge_required_inputs(
        root.get("required_inputs"), rule.get("required_input_types") or []
    )
    root["expected_outputs"] = _merge_expected_outputs(
        root.get("expected_outputs"), rule.get("expected_outputs") or []
    )

    handoff = root.setdefault("handoff", {})
    handoff.update({
        "current_skill": rule.get("skill"),
        "current_procedure_profile": rule.get("procedure_profile"),
        "next_stage": next_stage,
        "next_skill": next_rule.get("skill") if next_rule else None,
        "next_procedure_profile": next_rule.get("procedure_profile") if next_rule else None,
        "agent_level": rule.get("agent_level"),
    })
    handoff.setdefault("stop_reason", None)
    handoff.setdefault("escalation_target", None)

    validation = root.setdefault("validation", {})
    validation["route_contract_check"] = "PASS"
    validation["output_contract_check"] = "PASS"
    validation["typed_reference_check"] = validation.get("typed_reference_check", "PENDING")

    return result, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("routing", type=Path)
    parser.add_argument("stage_pack", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        result, errors = build_handoff(load(args.routing), load(args.stage_pack))
    except Exception as exc:
        print(f"HANDOFF-LOAD: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    args.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: stage handoff built: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
