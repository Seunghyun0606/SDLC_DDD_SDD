#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "sdlc" / "scripts"
SKILLS = ROOT / "sdlc" / "starter" / "onboarding-package-v1" / "skills"
FIXTURES = ROOT / "sdlc" / "design" / "validation" / "p0-runtime-core-redesign-v1" / "fixtures"
sys.path.insert(0, str(SCRIPTS))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_module("runtime_core", SCRIPTS / "execute_command_runtime.py")
router = load_module("runtime_router", SCRIPTS / "route_provider_command.py")
validator = load_module("runtime_validator", SCRIPTS / "validate_p0_runtime_core.py")
provider_validator = load_module("provider_validator", SCRIPTS / "validate_p06_contracts.py")
skill_validator = load_module("skill_validator", SCRIPTS / "validate_routed_skills.py")
handoff_builder = load_module("handoff_builder", SCRIPTS / "build_stage_handoff.py")
reverse_sync = load_module("reverse_sync", SCRIPTS / "build_reverse_sync_generic.py")
status_builder = load_module("status_builder", SCRIPTS / "build_status_view.py")


def load(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


def load_fixture(name):
    return yaml.safe_load((FIXTURES / name).read_text(encoding="utf-8")) or {}


def registry_with_states(source_state="UNCONFIGURED", test_state="UNCONFIGURED"):
    registry = load("sdlc/config/provider-registry.example.yaml")
    for provider in registry["registry"]["providers"]:
        if provider["provider_id"] == "source-primary":
            provider["provider_state"] = source_state
        if provider["provider_id"] == "test-primary":
            provider["provider_state"] = test_state
    return registry


def enable_source_write(registry):
    for provider in registry["registry"]["providers"]:
        if provider["provider_id"] == "source-write-primary":
            provider["enabled"] = True
            provider["provider_state"] = "AVAILABLE"
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


def assert_routing_references_exist(routing, procedures):
    profiles = set((procedures.get("profiles") or {}).keys())
    rules = list((routing.get("stages") or {}).values()) + [
        rule for command, rule in (routing.get("commands") or {}).items() if command != "/work"
    ]
    for rule in rules:
        skill = rule.get("skill")
        assert skill, rule
        assert (SKILLS / skill / "SKILL.md").is_file(), f"missing routed skill: {skill}"
        profile = rule.get("procedure_profile")
        if skill == "stage-procedure":
            assert profile in profiles, f"missing procedure profile: {profile}"
        deterministic_tool = rule.get("deterministic_tool")
        if deterministic_tool:
            assert (ROOT / deterministic_tool).is_file(), f"missing deterministic tool: {deterministic_tool}"


def assert_human_artifact_mapping(profile_doc):
    groups = profile_doc.get("human_document_groups") or {}
    satisfied = set()
    for group_name, group in groups.items():
        satisfied.update(group.get("satisfies") or [])
        if group.get("kind") == "TEMPLATE":
            path = group.get("template")
            assert path and (ROOT / path).is_file(), f"missing human template: {group_name} -> {path}"
        elif group.get("kind") == "GENERATED_VIEW":
            path = group.get("output")
            assert path, f"generated view path missing: {group_name}"
    for profile_name, profile in (profile_doc.get("profiles") or {}).items():
        for logical_role, policy in (profile.get("human_artifacts") or {}).items():
            if policy != "OFF":
                assert logical_role in satisfied, f"{profile_name}.{logical_role} has no document group mapping"


def make_completed_pack(template, routing, stage):
    pack = yaml.safe_load(yaml.safe_dump(template, allow_unicode=True))
    root = pack["stage_input_pack"]
    root["metadata"]["stage"] = stage
    built, errors = handoff_builder.build_handoff(routing, pack)
    assert errors == [], errors
    for output in built["stage_input_pack"]["expected_outputs"]:
        output["state"] = "COMPLETE"
        if output.get("artifact_id") == "OPEN":
            output["artifact_id"] = f"ART-{stage}-{output['output_type']}"
    return built


def main():
    routing = load("sdlc/config/stage-routing.yaml")
    procedures = load("sdlc/config/stage-procedures.yaml")
    pack = load("sdlc/templates/stage-input-pack.yaml")
    registry = load("sdlc/config/provider-registry.example.yaml")
    artifact_profiles = load("sdlc/config/artifact-profiles.yaml")

    assert validator.validate_stage_routing(routing) == []
    assert validator.validate_stage_procedures(procedures) == []
    assert validator.validate_routing_procedure_refs(routing, procedures) == []
    assert validator.validate_stage_pack(pack) == []
    assert provider_validator.validate_registry(registry) == []
    assert_routing_references_exist(routing, procedures)
    assert_human_artifact_mapping(artifact_profiles)
    for name in skill_validator.routed_skill_names(routing):
        assert skill_validator.validate_skill(SKILLS / name / "SKILL.md") == [], name

    # Handoff fields and expected outputs must be derived from routing, not invented by the next agent.
    impact_pack = yaml.safe_load(yaml.safe_dump(pack, allow_unicode=True))
    impact_pack["stage_input_pack"]["metadata"]["stage"] = "IMPACT"
    built, errors = handoff_builder.build_handoff(routing, impact_pack)
    assert errors == [], errors
    assert validator.validate_stage_pack(built) == []
    handoff = built["stage_input_pack"]["handoff"]
    outputs = built["stage_input_pack"]["expected_outputs"]
    assert handoff["current_skill"] == "stage-procedure"
    assert handoff["current_procedure_profile"] == "IMPACT"
    assert handoff["next_stage"] == "DESIGN"
    assert handoff["next_skill"] == "stage-procedure"
    assert handoff["next_procedure_profile"] == "DESIGN"
    assert any(item["output_type"] == "IMPACT_ANALYSIS" for item in outputs)
    assert any(item["input_type"] == "STAGE_INPUT_PACK" for item in built["stage_input_pack"]["required_inputs"])

    # Generic Greenfield must start without Source Provider or stack-specific configuration.
    greenfield = load_fixture("generic-greenfield-context.yaml")
    result = runtime.execute(registry_with_states(), greenfield, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert body["stage_route"]["stage"] == "INTAKE"
    assert body["stage_route"]["skill"] == "requirement-intake"
    assert body["stage_route"]["next_stage"] == "DECOMPOSE"

    # Generic Brownfield discovery with no Source/Analyzer Provider must remain PARTIAL/OPEN, not globally blocked.
    brownfield = load_fixture("generic-brownfield-context.yaml")
    result = runtime.execute(registry_with_states(), brownfield, routing)
    body = result["command_runtime_result"]
    assert body["stage_route"]["skill"] == "source-discovery"
    assert body["stage_route"]["next_stage"] == "IMPACT"
    assert body["state"] == "PARTIAL", body
    assert body["open_items"], body
    assert all(item.get("blocking") is False for item in body["open_items"]), body

    # Repeated document stages must use the consolidated procedure skill/profile.
    result = runtime.execute(registry_with_states(), context(stage="IMPACT", mode="GREENFIELD"), routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert body["stage_route"]["skill"] == "stage-procedure"
    assert body["stage_route"]["procedure_profile"] == "IMPACT"
    assert body["stage_route"]["next_stage"] == "DESIGN"

    # /change must request source.diff as optional Brownfield evidence and remain PARTIAL when unavailable.
    change_context = context(command="/change", stage="DEVELOPMENT", mode="BROWNFIELD")
    result = runtime.execute(registry_with_states(), change_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "PARTIAL", body
    assert body["stage_route"]["procedure_profile"] == "CHANGE_CONTROL"
    assert body["stage_route"]["deterministic_tool"] == "sdlc/scripts/build_reverse_sync_generic.py"
    assert any(item.get("capability") == "source.diff" and item.get("blocking") is False for item in body["open_items"]), body

    # Generic reverse sync traverses only confirmed trace edges and protects business truth.
    reverse, errors = reverse_sync.build(
        load_fixture("generic-brownfield-source-diff.yaml"),
        load_fixture("generic-brownfield-reference-graph.yaml"),
    )
    assert errors == [], errors
    reverse_root = reverse["reverse_sync_candidate"]
    assert reverse_root["protected_human_truth"] is True
    assert any(item["node_id"] == "ART-ORDER-001" and item["state"] == "STALE_CANDIDATE" for item in reverse_root["stale_candidates"])
    assert any(item["node_id"] == "FR-ORDER-001" and item["state"] == "REVIEW_CANDIDATE" for item in reverse_root["review_candidates"])
    assert any(item["node_id"] == "RQ-ORDER-001" and item["state"] == "REVIEW_CANDIDATE" for item in reverse_root["review_candidates"])

    # Source write is proposal-only by default and must be explicit, guarded, and preflighted.
    dev_default = context(stage="DEVELOPMENT", mode="GREENFIELD")
    result = runtime.execute(registry_with_states(), dev_default, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert "source.patch.apply" not in body["plan"]["runtime_plan"]["requested_capabilities"]

    dev_write = context(stage="DEVELOPMENT", mode="GREENFIELD")
    dev_write["requested_side_effect_capabilities"] = ["source.patch.apply"]
    result = runtime.execute(registry_with_states(), dev_write, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "INVALID", body
    assert any(error.startswith("ROUTE-WRITE-001") for error in body["errors"]), body

    dev_write["write_proofs"] = {
        "source.patch.apply": {
            "expected_revision": "ABSENT",
            "idempotency_key": "IDEMP-GF-001",
            "permission_proof_ref": "PERM-GF-001",
        }
    }
    result = runtime.execute(registry_with_states(), dev_write, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "ACTION_REQUIRED", body
    assert any(item.get("capability") == "source.patch.apply" and item.get("blocking") for item in body["open_items"]), body

    routed, route_errors = runtime.apply_stage_route(dev_write, routing)
    assert route_errors == [], route_errors
    write_registry = enable_source_write(registry_with_states())
    plan, plan_errors = router.build_plan(write_registry, routed)
    assert plan_errors == [], plan_errors
    assert plan["runtime_plan"]["status"] == "READY", plan
    assert any(
        item.get("capability") == "source.patch.apply" and item.get("provider_id") == "source-write-primary"
        for item in plan["runtime_plan"]["resolved_providers"]
    ), plan

    # /check must route to the full-stage read model and must not create truth.
    check_context = context(command="/check", stage="IMPACT", mode="GREENFIELD")
    result = runtime.execute(registry_with_states(), check_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert body["stage_route"]["procedure_profile"] == "STATUS_READ_MODEL"
    assert body["stage_route"]["deterministic_tool"] == "sdlc/scripts/build_status_view.py"
    intake_done = make_completed_pack(pack, routing, "INTAKE")
    decompose_done = make_completed_pack(pack, routing, "DECOMPOSE")
    status, errors = status_builder.build_status(routing, [intake_done, decompose_done])
    assert errors == [], errors
    status_root = status["sdlc_status_view"]
    assert status_root["current_stage"] == "CLARIFY"
    assert status_root["truth_guards"]["read_model_creates_truth"] is False
    assert len(status_root["stage_status"]) == 12

    # Test execution is a side effect. Missing proof fails before provider invocation.
    test_context = context(stage="TEST", mode="GREENFIELD")
    test_context["requested_side_effect_capabilities"] = ["test.execute"]
    result = runtime.execute(registry_with_states(), test_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "INVALID", body
    assert any(error.startswith("ROUTE-WRITE-001") for error in body["errors"]), body

    test_context["write_proofs"] = {
        "test.execute": {
            "expected_revision": "TEST-PLAN-001",
            "idempotency_key": "IDEMP-TEST-001",
            "permission_proof_ref": "PERM-TEST-001",
        }
    }
    result = runtime.execute(registry_with_states(), test_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "ACTION_REQUIRED", body
    assert any(item.get("capability") == "test.execute" and item.get("blocking") for item in body["open_items"]), body

    # /setup must be a valid administrator command in runtime and route through the shared procedure skill.
    setup_context = context(command="/setup", stage="INTAKE", mode="AUTO")
    result = runtime.execute(registry_with_states(), setup_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "COMPLETE", body
    assert body["stage_route"]["skill"] == "stage-procedure"
    assert body["stage_route"]["procedure_profile"] == "PROJECT_SETUP"
    assert body["stage_route"]["required_input_types"] == ["PROJECT_IDENTITY", "PROJECT_MODE", "PROVIDER_STATE"]

    # Unknown stage must fail deterministically instead of guessing.
    bad_context = context(stage="UNKNOWN_STAGE", mode="AUTO")
    result = runtime.execute(registry_with_states(), bad_context, routing)
    body = result["command_runtime_result"]
    assert body["state"] == "INVALID", body
    assert any(error.startswith("STAGE-ROUTE-002") for error in body["errors"]), body

    print("OK: P0 runtime core redesign conformance tests passed")


if __name__ == "__main__":
    main()
