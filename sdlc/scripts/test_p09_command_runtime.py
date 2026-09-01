#!/usr/bin/env python3
import sys
from pathlib import Path
from types import SimpleNamespace
from execute_command_runtime import execute


def reg():
    return {"registry": {"providers": [
        {
            "provider_id": "router",
            "provider_type": "COMMAND_ROUTER",
            "enabled": True,
            "provider_state": "AVAILABLE",
            "mode": "READ_ONLY",
            "capabilities": ["command.route.work", "command.route.change", "command.route.check", "command.route.setup"],
        },
        {
            "provider_id": "generic",
            "provider_type": "GENERIC",
            "enabled": True,
            "provider_state": "AVAILABLE",
            "mode": "READ_ONLY",
            "capabilities": ["generic.read"],
            "extensions": {"module": "fake.cmd.adapter"},
        },
        {
            "provider_id": "source-writer",
            "provider_type": "SOURCE",
            "enabled": True,
            "provider_state": "AVAILABLE",
            "mode": "READ_WRITE",
            "capabilities": ["source.patch.apply"],
            "extensions": {"module": "fake.cmd.source"},
        },
    ]}}


def ctx(command="/check", caps=None, stage="INTAKE"):
    return {
        "command_id": "CMD-X",
        "command": command,
        "project_context": {"project_id": "P", "mode": "BROWNFIELD", "stage": stage},
        "target": {"target_type": "WORK_UNIT", "target_id": "W"},
        "requested_capabilities": caps or [],
        "optional_capabilities": [],
        "requested_side_effect_capabilities": [],
        "write_capabilities": [],
        "capability_inputs": {},
        "write_proofs": {},
        "human_actions": [],
        "adapter_configs": {},
    }


def ok(req, cfg):
    r = req["provider_request"]
    return {"provider_response": {
        "request_id": r["request_id"],
        "provider_id": "generic",
        "provider_type": "GENERIC",
        "operation": r["operation"],
        "status": "OK",
        "provider_revision": "rev",
        "outputs": [],
        "evidence": [],
        "open_items": [],
        "warnings": [],
        "retryable": False,
        "extensions": {},
    }}


def main():
    sys.modules["fake.cmd.adapter"] = SimpleNamespace(invoke=ok)

    r = execute(reg(), ctx())
    assert r["command_runtime_result"]["state"] == "COMPLETE" and not r["command_runtime_result"]["invocations"]

    r = execute(reg(), ctx("/work", ["generic.read"], "INTAKE"))
    assert r["command_runtime_result"]["state"] == "COMPLETE" and len(r["command_runtime_result"]["invocations"]) == 1

    r = execute(reg(), ctx("/work", ["missing.capability"], "INTAKE"))
    assert r["command_runtime_result"]["state"] == "ACTION_REQUIRED" and not r["command_runtime_result"]["invocations"]

    c = ctx("/work", ["generic.read"], "INTAKE")
    c["human_actions"] = [{"action_type": "DECISION", "owner": "HUMAN", "blocks_action": True}]
    r = execute(reg(), c)
    assert r["command_runtime_result"]["state"] == "ACTION_REQUIRED" and not r["command_runtime_result"]["invocations"]

    c["human_actions"][0]["blocks_action"] = False
    r = execute(reg(), c)
    assert r["command_runtime_result"]["state"] == "COMPLETE" and r["command_runtime_result"]["invocations"]

    # Legacy direct write_capability injection is no longer a valid bypass.
    bypass = ctx("/work", ["generic.read"], "INTAKE")
    bypass["write_capabilities"] = ["generic.write"]
    r = execute(reg(), bypass)
    assert r["command_runtime_result"]["state"] == "INVALID"
    assert any(x.startswith("STAGE-ROUTE-004") for x in r["command_runtime_result"]["errors"])

    # Explicit, stage-allowed source write still preserves UNKNOWN_AFTER_WRITE recovery.
    def boom(req, cfg):
        raise RuntimeError("response lost")

    sys.modules["fake.cmd.source"] = SimpleNamespace(invoke=boom)
    c = ctx("/work", [], "DEVELOPMENT")
    c["requested_side_effect_capabilities"] = ["source.patch.apply"]
    c["write_proofs"] = {
        "source.patch.apply": {
            "expected_revision": "r1",
            "idempotency_key": "i1",
            "permission_proof_ref": "p1",
        }
    }
    r = execute(reg(), c)
    assert r["command_runtime_result"]["state"] == "RECOVERY_REQUIRED", r

    root = Path(__file__).resolve().parents[1]
    forbidden = ["REQ_TM_TE", "RQG-CAND-6BB6D66548", "근태", "AttendanceClose", "TB_ATT_", "10분"]
    for rel in [
        "design/contracts/command-runtime-integration.md",
        "templates/command-runtime-context.yaml",
        "scripts/execute_command_runtime.py",
    ]:
        text = (root / rel).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (rel, token)

    print("OK: P0.9 command runtime integration tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
