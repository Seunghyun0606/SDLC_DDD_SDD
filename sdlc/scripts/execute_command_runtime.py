#!/usr/bin/env python3
"""Execute SDLC commands through config-driven stage routing and provider invocation."""
from __future__ import annotations
import argparse
import copy
from pathlib import Path
from typing import Any
import yaml
from route_provider_command import build_plan
from invoke_provider_runtime import invoke_request

DEFAULT_STAGE_ROUTING = Path(__file__).resolve().parents[1] / "config" / "stage-routing.yaml"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unique(values):
    out = []
    for value in values or []:
        if value and value not in out:
            out.append(value)
    return out


def apply_stage_route(context: dict[str, Any], routing: dict[str, Any]):
    routed = copy.deepcopy(context)
    command = routed.get("command")
    commands = routing.get("commands") or {}
    command_rule = commands.get(command)
    if not command_rule:
        return routed, [f"STAGE-ROUTE-001: unsupported command: {command}"]

    required = list(routed.get("requested_capabilities") or [])
    optional = list(routed.get("optional_capabilities") or [])
    route_summary: dict[str, Any] = {
        "command": command,
        "procedure_config": routing.get("procedure_config"),
    }

    if command == "/work":
        project = routed.setdefault("project_context", {})
        stage = project.get("stage") or command_rule.get("default_stage")
        stages = routing.get("stages") or {}
        stage_rule = stages.get(stage)
        if not stage_rule:
            return routed, [f"STAGE-ROUTE-002: unknown project_context.stage: {stage}"]
        project["stage"] = stage
        mode = str(project.get("mode") or "AUTO").upper()
        for candidate in stage_rule.get("capability_candidates") or []:
            modes = [str(x).upper() for x in (candidate.get("modes") or [])]
            if modes and mode not in modes:
                continue
            capability = candidate.get("capability")
            if not capability:
                continue
            if candidate.get("missing_behavior") == "BLOCKED":
                required.append(capability)
            else:
                optional.append(capability)

        allowed_side_effects = set(stage_rule.get("side_effect_capabilities") or [])
        requested_side_effects = set(routed.get("requested_side_effect_capabilities") or [])
        unknown_side_effects = sorted(requested_side_effects - allowed_side_effects)
        if unknown_side_effects:
            return routed, [f"STAGE-ROUTE-003: side-effect capabilities not allowed in {stage}: {unknown_side_effects}"]
        required.extend(sorted(requested_side_effects))
        routed["write_capabilities"] = _unique(list(routed.get("write_capabilities") or []) + sorted(requested_side_effects))

        route_summary.update({
            "stage": stage,
            "display_name_ko": stage_rule.get("display_name_ko"),
            "skill": stage_rule.get("skill"),
            "procedure_profile": stage_rule.get("procedure_profile"),
            "agent_level": stage_rule.get("agent_level"),
            "required_input_types": stage_rule.get("required_input_types") or [],
            "expected_outputs": stage_rule.get("expected_outputs") or [],
            "next_stage": stage_rule.get("next_stage"),
        })
    else:
        route_summary.update({
            "skill": command_rule.get("skill"),
            "procedure_profile": command_rule.get("procedure_profile"),
            "agent_level": command_rule.get("agent_level"),
            "required_input_types": command_rule.get("required_input_types") or [],
            "expected_outputs": command_rule.get("expected_outputs") or [],
        })

    routed["requested_capabilities"] = _unique(required)
    routed["optional_capabilities"] = [x for x in _unique(optional) if x not in routed["requested_capabilities"]]
    routed["stage_route"] = route_summary
    return routed, []


def execute(registry: dict[str, Any], context: dict[str, Any], stage_routing: dict[str, Any] | None = None):
    routing = stage_routing if stage_routing is not None else load(DEFAULT_STAGE_ROUTING)
    routed_context, route_errors = apply_stage_route(context, routing)
    if route_errors:
        return {"command_runtime_result": {
            "command_id": context.get("command_id"),
            "state": "INVALID",
            "stage_route": routed_context.get("stage_route"),
            "plan": {},
            "errors": route_errors,
            "invocations": [],
            "open_items": [],
        }}

    plan, errors = build_plan(registry, routed_context)
    if errors:
        return {"command_runtime_result": {
            "command_id": routed_context.get("command_id"),
            "state": "INVALID",
            "stage_route": routed_context.get("stage_route"),
            "plan": plan,
            "errors": errors,
            "invocations": [],
            "open_items": [],
        }}

    runtime = plan.get("runtime_plan") or {}
    open_items = list(runtime.get("open_items") or [])
    blocking_open = [item for item in open_items if item.get("blocking")]
    human_actions = list(routed_context.get("human_actions") or [])
    blocking_human = [item for item in human_actions if item.get("blocks_action", True)]
    resolved = list(runtime.get("resolved_providers") or [])
    invocations = []
    capability_inputs = routed_context.get("capability_inputs") or {}
    write_caps = set(routed_context.get("write_capabilities") or [])
    proofs = routed_context.get("write_proofs") or {}
    adapter_configs = routed_context.get("adapter_configs") or {}

    if blocking_open or blocking_human:
        return {"command_runtime_result": {
            "command_id": routed_context.get("command_id"),
            "state": "ACTION_REQUIRED",
            "stage_route": routed_context.get("stage_route"),
            "plan": plan,
            "errors": [],
            "invocations": [],
            "open_items": open_items,
            "human_actions": human_actions,
        }}

    external = [item for item in resolved if item.get("provider_type") != "COMMAND_ROUTER"]
    for idx, item in enumerate(external, 1):
        capability = item.get("capability")
        write = capability in write_caps
        proof = proofs.get(capability) or {}
        request = {"provider_request": {
            "request_id": f"{routed_context.get('command_id', 'CMD')}-REQ-{idx:02d}",
            "provider_type": item.get("provider_type"),
            "operation": capability,
            "project_context": routed_context.get("project_context") or {},
            "target": routed_context.get("target") or {},
            "inputs": [],
            "write_intent": write,
            "expected_revision": proof.get("expected_revision"),
            "idempotency_key": proof.get("idempotency_key"),
            "permission_proof_ref": proof.get("permission_proof_ref"),
            "constraints": {"do_not_invent_missing_result": True},
            "extensions": capability_inputs.get(capability) or {},
        }}
        journal, response = invoke_request(registry, request, adapter_configs)
        invocations.append({"capability": capability, "request": request, "journal": journal, "response": response})

    states = [item["journal"]["invocation_journal"]["state"] for item in invocations]
    if "UNKNOWN_AFTER_WRITE" in states:
        state = "RECOVERY_REQUIRED"
    elif any(value in {"BLOCKED", "FAILED"} for value in states):
        state = "ACTION_REQUIRED"
    elif "PARTIAL" in states or open_items:
        state = "PARTIAL"
    else:
        state = "COMPLETE"

    return {"command_runtime_result": {
        "command_id": routed_context.get("command_id"),
        "command": routed_context.get("command"),
        "state": state,
        "stage_route": routed_context.get("stage_route"),
        "plan": plan,
        "errors": [],
        "invocations": invocations,
        "open_items": open_items,
        "human_actions": human_actions,
    }}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("context", type=Path)
    parser.add_argument("--stage-routing", type=Path, default=DEFAULT_STAGE_ROUTING)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = execute(load(args.registry), load(args.context), load(args.stage_routing))
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["command_runtime_result"]["state"] in {"COMPLETE", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
