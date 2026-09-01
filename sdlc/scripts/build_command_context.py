#!/usr/bin/env python3
"""Build command-runtime context directly from a Stage Input Pack and Stage Execution Plan."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build(stage_pack_doc: dict[str, Any], execution_plan_doc: dict[str, Any], command: str) -> dict[str, Any]:
    pack = (stage_pack_doc or {}).get("stage_input_pack") or {}
    meta = pack.get("metadata") or {}
    target = pack.get("target") or {}
    execution = pack.get("execution") or {}
    plan = (execution_plan_doc or {}).get("stage_execution") or {}
    if plan.get("pack_id") != meta.get("pack_id"):
        raise ValueError("stage execution plan pack_id does not match stage input pack")

    required = list(plan.get("required_capabilities") or [])
    requested = list(plan.get("requested_capabilities") or [])
    writes = list(plan.get("write_capabilities") or [])
    write_proofs = execution.get("write_proofs") or {}

    missing_proofs = []
    for capability in writes:
        proof = write_proofs.get(capability) or {}
        if not proof.get("expected_revision"):
            missing_proofs.append({"capability": capability, "missing": "expected_revision"})
        if not proof.get("idempotency_key"):
            missing_proofs.append({"capability": capability, "missing": "idempotency_key"})
        if not proof.get("permission_proof_ref"):
            missing_proofs.append({"capability": capability, "missing": "permission_proof_ref"})

    human_actions = list(execution.get("human_actions") or [])
    for missing in missing_proofs:
        human_actions.append({
            "action_id": f"PROOF-{missing['capability']}-{missing['missing']}",
            "type": "WRITE_PROOF_REQUIRED",
            "capability": missing["capability"],
            "missing": missing["missing"],
            "blocks_action": True,
        })

    revision_guard = execution.get("revision_guard") or {}
    if "source.write" in writes:
        guard_ok = revision_guard.get("decision") == "ALLOW" and bool(revision_guard.get("guard_proof_ref"))
        if not guard_ok:
            human_actions.append({
                "action_id": "SOURCE-WRITE-REVISION-OWNERSHIP-GUARD",
                "type": "REVISION_OWNERSHIP_GUARD_REQUIRED",
                "capability": "source.write",
                "blocks_action": True,
                "required_evidence": ["revision_ownership_guard.decision=ALLOW", "guard_proof_ref"],
            })

    return {
        "schema_version": 3,
        "command_id": f"CMD-{meta.get('pack_id') or 'UNASSIGNED'}",
        "command": command,
        "project_context": {
            "project_id": meta.get("project_id"),
            "mode": meta.get("project_mode") or "AUTO",
            "stage": meta.get("stage"),
            "profile": meta.get("profile"),
            "source_revision": meta.get("source_revision"),
        },
        "target": {
            "target_type": target.get("target_type"),
            "target_id": target.get("primary_id"),
            "related_ids": target.get("related_ids") or {},
        },
        "requested_capabilities": requested,
        "required_capabilities": required,
        "write_capabilities": writes,
        "write_intent": bool(writes),
        "permission_proof_ref": "STAGE_SCOPED" if writes and not missing_proofs else None,
        "idempotency_key": "STAGE_SCOPED" if writes and not missing_proofs else None,
        "capability_inputs": execution.get("capability_inputs") or {},
        "write_proofs": write_proofs,
        "human_actions": human_actions,
        "adapter_configs": execution.get("adapter_configs") or {},
        "revision_guard": {
            "decision": revision_guard.get("decision") or "NOT_EVALUATED",
            "guard_proof_ref": revision_guard.get("guard_proof_ref"),
        },
        "stage_execution": {
            "skill": plan.get("skill"),
            "expected_outputs": plan.get("expected_outputs") or [],
            "next_stage": plan.get("next_stage"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage_pack", type=Path)
    parser.add_argument("execution_plan", type=Path)
    parser.add_argument("--command", default="/work", choices=["/work", "/change", "/check"])
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = build(load(args.stage_pack), load(args.execution_plan), args.command)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
