#!/usr/bin/env python3
"""Validate P0 redesigned stage routing, procedure profiles, and typed Stage Input Pack contracts."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml

STAGES = [
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE",
]
PROCEDURE_PROFILES = {
    "DECOMPOSE", "CLARIFY", "PROCESS", "IMPACT", "DESIGN", "PROGRAM", "KNOWLEDGE",
    "CHANGE_CONTROL", "STATUS_READ_MODEL", "PROJECT_SETUP",
}
RELATED_KEYS = {
    "rq", "fr", "br", "proc", "ftr", "pgm", "art", "symbol", "data", "int",
    "ac", "tc", "task", "cr", "knowledge", "source",
}
TRUTH_STATES = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
INPUT_STATES = {"AVAILABLE", "OPEN", "NOT_APPLICABLE"}
OUTPUT_STATES = {"PLANNED", "PARTIAL", "COMPLETE", "OPEN"}
AGENT_LEVELS = {
    "L1_AGENT_READY", "L1_WITH_DETERMINISTIC_GUARDS", "L2_AGENT_REQUIRED", "HUMAN_REQUIRED",
}


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def add(errors, code, message):
    errors.append(f"{code}: {message}")


def nonempty(value):
    return value is not None and value != "" and value != [] and value != {}


def validate_stage_routing(doc):
    errors = []
    order = doc.get("stage_order") or []
    stages = doc.get("stages") or {}
    commands = doc.get("commands") or {}
    principles = doc.get("principles") or {}

    if order != STAGES:
        add(errors, "PRC-001", f"stage_order must be exactly {STAGES}")
    if set(stages) != set(STAGES):
        add(errors, "PRC-002", "stages keys must exactly match stage_order")
    for command in ("/work", "/change", "/check", "/setup"):
        if command not in commands:
            add(errors, "PRC-003", f"commands.{command} is required")
    if principles.get("config_driven_stage_selection") is not True:
        add(errors, "PRC-004", "config_driven_stage_selection must be true")
    if principles.get("missing_read_capability_preserves_open") is not True:
        add(errors, "PRC-005", "missing read capability must preserve OPEN")
    if principles.get("repeated_document_stages_use_shared_skill") is not True:
        add(errors, "PRC-006", "repeated document stages must use the shared procedure skill")
    if not nonempty(doc.get("procedure_config")):
        add(errors, "PRC-007", "procedure_config is required")

    for index, stage in enumerate(STAGES):
        rule = stages.get(stage) or {}
        for key in ("display_name_ko", "skill", "agent_level", "required_input_types", "expected_outputs"):
            if not nonempty(rule.get(key)):
                add(errors, "PRC-010", f"stages.{stage}.{key} is required")
        if rule.get("agent_level") not in AGENT_LEVELS:
            add(errors, "PRC-011", f"stages.{stage}.agent_level is invalid")
        expected_next = STAGES[index + 1] if index + 1 < len(STAGES) else None
        if rule.get("next_stage") != expected_next:
            add(errors, "PRC-012", f"stages.{stage}.next_stage must be {expected_next}")
        if rule.get("skill") == "stage-procedure" and not nonempty(rule.get("procedure_profile")):
            add(errors, "PRC-015", f"stages.{stage}.procedure_profile is required for stage-procedure")
        for candidate in rule.get("capability_candidates") or []:
            if not nonempty(candidate.get("capability")):
                add(errors, "PRC-013", f"stages.{stage} has capability candidate without capability")
            if candidate.get("missing_behavior") not in {"OPEN", "BLOCKED"}:
                add(errors, "PRC-014", f"stages.{stage} capability missing_behavior must be OPEN or BLOCKED")

    for command in ("/change", "/check", "/setup"):
        rule = commands.get(command) or {}
        if rule.get("skill") == "stage-procedure" and not nonempty(rule.get("procedure_profile")):
            add(errors, "PRC-016", f"commands.{command}.procedure_profile is required")
        if rule.get("agent_level") not in AGENT_LEVELS:
            add(errors, "PRC-017", f"commands.{command}.agent_level is invalid")

    boundary = doc.get("analyzer_boundary") or {}
    if boundary.get("core_must_not_parse_stack_specific_syntax") is not True:
        add(errors, "PRC-020", "Core must not parse stack-specific syntax")
    if not nonempty(boundary.get("stack_specific_analysis_location")):
        add(errors, "PRC-021", "stack_specific_analysis_location is required")
    return errors


def validate_stage_procedures(doc):
    errors = []
    profiles = doc.get("profiles") or {}
    if set(profiles) != PROCEDURE_PROFILES:
        missing = sorted(PROCEDURE_PROFILES - set(profiles))
        extra = sorted(set(profiles) - PROCEDURE_PROFILES)
        add(errors, "PROC-001", f"procedure profiles mismatch; missing={missing}, extra={extra}")
    for name, profile in profiles.items():
        profile = profile or {}
        for key in ("purpose_ko", "atomic_steps", "decision_rules", "quality_checks", "alerts", "stop_conditions", "escalation", "do_not"):
            if key not in profile:
                add(errors, "PROC-002", f"profiles.{name}.{key} is required")
        for key in ("purpose_ko", "atomic_steps", "decision_rules", "quality_checks", "stop_conditions", "do_not"):
            if not nonempty(profile.get(key)):
                add(errors, "PROC-003", f"profiles.{name}.{key} must not be empty")
    return errors


def validate_routing_procedure_refs(routing, procedures):
    errors = []
    profile_names = set((procedures.get("profiles") or {}).keys())
    for stage, rule in (routing.get("stages") or {}).items():
        if rule.get("skill") == "stage-procedure" and rule.get("procedure_profile") not in profile_names:
            add(errors, "BUNDLE-001", f"stage {stage} references missing procedure profile {rule.get('procedure_profile')}")
    for command, rule in (routing.get("commands") or {}).items():
        if command == "/work":
            continue
        if rule.get("skill") == "stage-procedure" and rule.get("procedure_profile") not in profile_names:
            add(errors, "BUNDLE-002", f"command {command} references missing procedure profile {rule.get('procedure_profile')}")
    return errors


def validate_stage_pack(doc):
    errors = []
    if doc.get("version") != 2:
        add(errors, "SIP2-001", "Stage Input Pack version must be 2")
    root = doc.get("stage_input_pack") or {}
    meta = root.get("metadata") or {}
    target = root.get("target") or {}
    related = target.get("related_ids") or {}

    for key in ("pack_id", "project_id", "stage", "source_revision", "profile", "route_revision"):
        if not nonempty(meta.get(key)):
            add(errors, "SIP2-002", f"metadata.{key} is required")
    if meta.get("stage") not in STAGES and meta.get("stage") != "FILL_ME":
        add(errors, "SIP2-003", "metadata.stage must be a known stage")
    if not RELATED_KEYS.issubset(set(related)):
        add(errors, "SIP2-004", f"target.related_ids must include {sorted(RELATED_KEYS)}")

    for idx, item in enumerate(root.get("required_inputs") or []):
        if not nonempty(item.get("input_type")) or not nonempty(item.get("ref")):
            add(errors, "SIP2-010", f"required_inputs[{idx}] requires input_type and ref")
        if item.get("required") not in {True, False}:
            add(errors, "SIP2-011", f"required_inputs[{idx}].required must be boolean")
        if item.get("state") not in INPUT_STATES:
            add(errors, "SIP2-012", f"required_inputs[{idx}].state is invalid")

    evidence_ids = set()
    for idx, item in enumerate(root.get("evidence") or []):
        for key in ("evidence_id", "evidence_type", "truth", "locator", "revision"):
            if not nonempty(item.get(key)):
                add(errors, "SIP2-020", f"evidence[{idx}].{key} is required")
        if item.get("truth") not in {"GIVEN", "OBSERVED"}:
            add(errors, "SIP2-021", f"evidence[{idx}].truth must be GIVEN or OBSERVED")
        eid = item.get("evidence_id")
        if eid in evidence_ids:
            add(errors, "SIP2-022", f"duplicate evidence_id: {eid}")
        evidence_ids.add(eid)

    for idx, fact in enumerate(root.get("resolved_facts") or []):
        for key in ("fact_id", "fact_type", "truth"):
            if not nonempty(fact.get(key)):
                add(errors, "SIP2-030", f"resolved_facts[{idx}].{key} is required")
        if fact.get("truth") not in TRUTH_STATES:
            add(errors, "SIP2-031", f"resolved_facts[{idx}].truth is invalid")
        missing = [ref for ref in fact.get("evidence_ids") or [] if ref not in evidence_ids]
        if missing:
            add(errors, "SIP2-032", f"resolved_facts[{idx}] references missing evidence: {missing}")
        if fact.get("truth") == "CONFIRMED" and not (fact.get("evidence_ids") or []):
            add(errors, "SIP2-033", f"resolved_facts[{idx}] CONFIRMED requires evidence")

    for idx, output in enumerate(root.get("expected_outputs") or []):
        if not nonempty(output.get("output_type")):
            add(errors, "SIP2-040", f"expected_outputs[{idx}].output_type is required")
        if output.get("required") not in {True, False}:
            add(errors, "SIP2-041", f"expected_outputs[{idx}].required must be boolean")
        if output.get("state") not in OUTPUT_STATES:
            add(errors, "SIP2-042", f"expected_outputs[{idx}].state is invalid")

    handoff = root.get("handoff") or {}
    for key in ("current_skill", "agent_level"):
        if not nonempty(handoff.get(key)):
            add(errors, "SIP2-050", f"handoff.{key} is required")
    if handoff.get("agent_level") not in AGENT_LEVELS and handoff.get("agent_level") != "FILL_ME":
        add(errors, "SIP2-051", "handoff.agent_level is invalid")

    constraints = root.get("constraints") or {}
    required_guards = (
        "do_not_invent_missing_business_fact",
        "source_behavior_is_not_business_truth",
        "ambiguous_write_must_not_be_auto_selected",
        "candidate_is_not_canonical",
        "runtime_pass_requires_execution_evidence",
        "provider_partial_must_remain_partial",
    )
    for key in required_guards:
        if constraints.get(key) is not True:
            add(errors, "SIP2-060", f"constraints.{key} must be true")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["routing", "procedures", "stage-pack", "bundle"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--procedures", type=Path)
    args = parser.parse_args()

    doc = load(args.path)
    if args.kind == "routing":
        errors = validate_stage_routing(doc)
    elif args.kind == "procedures":
        errors = validate_stage_procedures(doc)
    elif args.kind == "stage-pack":
        errors = validate_stage_pack(doc)
    else:
        if not args.procedures:
            print("BUNDLE-000: --procedures is required for bundle validation")
            return 1
        procedures = load(args.procedures)
        errors = validate_stage_routing(doc) + validate_stage_procedures(procedures) + validate_routing_procedure_refs(doc, procedures)

    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: P0 runtime core {args.kind} valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
