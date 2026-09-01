#!/usr/bin/env python3
"""Build a deterministic provider runtime plan without invoking providers."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any
import yaml

COMMAND_CAPABILITY = {
    "/work": "command.route.work",
    "/change": "command.route.change",
    "/check": "command.route.check",
    "/setup": "command.route.setup",
}
USABLE_PROVIDER_STATES = {"AVAILABLE", "DEGRADED"}
WRITE_PROOF_FIELDS = ("expected_revision", "idempotency_key", "permission_proof_ref")


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def select(registry: dict[str, Any], capability: str, write_intent: bool = False):
    declared, usable = [], []
    for provider in ((registry.get("registry") or {}).get("providers") or []):
        if capability not in (provider.get("capabilities") or []):
            continue
        declared.append(provider)
        if provider.get("enabled") is not True:
            continue
        if provider.get("provider_state") not in USABLE_PROVIDER_STATES:
            continue
        if write_intent and provider.get("mode") != "READ_WRITE":
            continue
        usable.append(provider)
    if not usable:
        return None, "PROVIDER_UNAVAILABLE" if declared else "MISSING_CAPABILITY"
    ranked = sorted(usable, key=lambda p: (int(p.get("priority", 100)), str(p.get("provider_id"))))
    if len(ranked) > 1 and int(ranked[0].get("priority", 100)) == int(ranked[1].get("priority", 100)):
        return None, "AMBIGUOUS_PROVIDER"
    return ranked[0], None


def _unique(values):
    out = []
    for value in values or []:
        if value and value not in out:
            out.append(value)
    return out


def _validate_write_proofs(context: dict[str, Any], write_caps: set[str]):
    errors = []
    proofs = context.get("write_proofs") or {}
    for capability in sorted(write_caps):
        proof = proofs.get(capability) or {}
        for field in WRITE_PROOF_FIELDS:
            if not proof.get(field):
                errors.append(f"ROUTE-WRITE-001: {capability} requires write_proofs.{capability}.{field}")
    return errors


def build_plan(registry: dict[str, Any], context: dict[str, Any]):
    errors = []
    command = context.get("command")
    if command not in COMMAND_CAPABILITY:
        return {}, ["ROUTE-001: command must be /work, /change, /check, or /setup"]

    router_capability = COMMAND_CAPABILITY[command]
    required = _unique([router_capability] + list(context.get("requested_capabilities") or []))
    optional = [cap for cap in _unique(context.get("optional_capabilities") or []) if cap not in required]
    write_caps = set(context.get("write_capabilities") or [])
    errors.extend(_validate_write_proofs(context, write_caps))

    resolved, open_items = [], []
    for requirement, capabilities in (("REQUIRED", required), ("OPTIONAL", optional)):
        for capability in capabilities:
            provider, problem = select(registry, capability, capability in write_caps)
            if problem:
                open_items.append({
                    "capability": capability,
                    "reason": problem,
                    "requirement": requirement,
                    "blocking": requirement == "REQUIRED",
                })
                continue
            resolved.append({
                "capability": capability,
                "requirement": requirement,
                "provider_id": provider.get("provider_id"),
                "provider_type": provider.get("provider_type"),
                "provider_state": provider.get("provider_state"),
                "mode": provider.get("mode"),
            })

    human_actions = list(context.get("human_actions") or [])
    blocking_human = [item for item in human_actions if item.get("blocks_action", True)]
    blocking_open = [item for item in open_items if item.get("blocking")]
    status = "READY" if not blocking_open and not blocking_human else "ACTION_REQUIRED"

    # Compatibility guard for callers that still use the legacy top-level write_intent fields.
    if context.get("write_intent") and not context.get("permission_proof_ref"):
        errors.append("ROUTE-002: write_intent requires permission_proof_ref")
    if context.get("write_intent") and not context.get("idempotency_key"):
        errors.append("ROUTE-003: write_intent requires idempotency_key")

    plan = {
        "schema_version": 3,
        "artifact_type": "PROVIDER_RUNTIME_PLAN",
        "runtime_plan": {
            "plan_id": context.get("plan_id", "PLAN-RUNTIME-001"),
            "command": command,
            "project_context": context.get("project_context") or {},
            "target": context.get("target") or {},
            "requested_capabilities": required,
            "optional_capabilities": optional,
            "write_capabilities": sorted(write_caps),
            "resolved_providers": resolved,
            "human_actions": human_actions,
            "open_items": open_items,
            "executable": status == "READY" and not errors,
            "write_intent": bool(write_caps) or bool(context.get("write_intent")),
            "status": "INVALID" if errors else status,
        },
    }
    return plan, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("context", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        plan, errors = build_plan(load(args.registry), load(args.context))
    except Exception as exc:
        print(f"ROUTE-LOAD: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    text = yaml.safe_dump(plan, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
