#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "sdlc" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_module("runtime_core", SCRIPTS / "execute_command_runtime.py")
validator = load_module("runtime_validator", SCRIPTS / "validate_p0_runtime_core.py")


def load(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


def registry_with_states(source_state="UNCONFIGURED", test_state="UNCONFIGURED"):
    registry = load("sdlc/config/provider-registry.example.yaml")
    for provider in registry["registry"]["providers"]:
        if provider["provider_id"] == "source-primary":
            provider["provider_state"] = source_state
        if provider["provider_id"] == "test-primary":
            provider["provider_state"] = test_state
    return registry


def context(command="/work", stage="INTAKE", mode="AUTO"):
    return {
        "schema_version": 2,
        "command_id": "CMD-P0-REDESIGN-001",
        "command": command,
        "project_context": {"project_id": "DEMO-GENERIC-001", "mode": mode, "stage": stage},
        "target": {"target_type": "WORK_UNIT", "target_id": "DEMO-WORK-001"},
        "requested_capabilities": [],
        "optional_capabilities": [],
        "requested_side_effect_capabilities": [],
        "write_capabilities": [],
        "capability_inputs": {},
        "write_proofs": {},
        "human_actions": [],
        "adapter_configs": {},
    }


def main():
    routing = load("sdlc/config/stage-routing.yaml")
    pack = load("sdlc/templates/stage-input-pack.yaml")
    assert validator.validate_stage_routing(routing) == []
    assert validator.validate_stage_pack(pack) == []

    # Brownfield discovery with no Source Provider must remain PARTIAL/OPEN, not globally blocked.
    result = runtime.execute(registry_with_states(), context(stage="DISCOVERY", mode="BROWNFIELD"), routing)
    body = result["command_runtime_result"]
    assert body["stage_route"]["skill"] == "source-discovery"
    assert body["stage_route"]["next_stage"] == "IMPACT"
    assert body["state"] == "PARTIAL", body
    assert body["open_items"], body
    assert all(item.get("blocking") is False for item in body["open_items"]), body

    # Test execution is a side effect. If explicitly requested with unavailable TEST Provider, it must block that action.
    test_context = context(stage="TEST", mode="GREENFIELD")
    test_context["requested_side_effect_capabilities"] = ["test.execute"]
    result = runtime.execute(registry_with_states(), test_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "ACTION_REQUIRED", body
    assert any(item.get("capability") == "test.execute" and item.get("blocking") for item in body["open_items"]), body

    # /setup must be a valid administrator command in runtime.
    setup_context = context(command="/setup", stage="INTAKE", mode="AUTO")
    result = runtime.execute(registry_with_states(), setup_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert body["stage_route"]["skill"] == "project-foundation-bootstrap"

    # Unknown stage must fail deterministically instead of guessing.
    bad_context = context(stage="UNKNOWN_STAGE", mode="AUTO")
    result = runtime.execute(registry_with_states(), bad_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "INVALID", body
    assert any(error.startswith("STAGE-ROUTE-002") for error in body["errors"]), body

    print("OK: P0 runtime core redesign conformance tests passed")


if __name__ == "__main__":
    main()
