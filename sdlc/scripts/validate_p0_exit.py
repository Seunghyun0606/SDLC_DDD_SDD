#!/usr/bin/env python3
"""Validate the P0 design baseline exit gate. Sample/pilot artifacts are not required inputs."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def add(errors: list[str], code: str, msg: str) -> None:
    errors.append(f"{code}: {msg}")


def validate(root: Path, gate: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cfg = (gate or {}).get("p0_exit_gate") or {}
    required = list(cfg.get("required_paths") or []) + list(cfg.get("required_test_definitions") or [])
    missing = [rel for rel in required if not (root / rel).exists()]
    for rel in missing:
        add(errors, "P0X-001", f"required path missing: {rel}")

    index_path = root / "sdlc/config/baseline-contract-index.yaml"
    if index_path.exists():
        index = load(index_path)
        roles = index.get("baseline_roles") or {}
        for name, role in roles.items():
            authority = (role or {}).get("authority")
            if authority and not (root / authority).exists():
                add(errors, "P0X-002", f"baseline index {name} authority missing: {authority}")
        ownership = index.get("truth_ownership") or {}
        if ownership.get("index_is_authoritative_for_content") is not False or ownership.get("duplicate_truth_in_index") != "DENY":
            add(errors, "P0X-003", "baseline index must remain non-authoritative and deny duplicate truth")

    registry_path = root / "sdlc/config/provider-registry.example.yaml"
    if registry_path.exists():
        reg = (load(registry_path).get("registry") or {}).get("providers") or []
        for p in reg:
            if p.get("provider_type") in {"SOURCE", "TEST"} and p.get("provider_state") == "AVAILABLE":
                add(errors, "P0X-004", "example SOURCE/TEST provider must not default to AVAILABLE")

    invocation_path = root / "sdlc/config/runtime-invocation.yaml"
    if invocation_path.exists():
        inv = load(invocation_path).get("runtime_invocation") or {}
        if (inv.get("write_retry") or {}).get("enabled") is not False:
            add(errors, "P0X-005", "write retry must be disabled by default")
        if (inv.get("write_retry") or {}).get("unknown_after_dispatch_state") != "UNKNOWN_AFTER_WRITE":
            add(errors, "P0X-006", "unknown write state must be UNKNOWN_AFTER_WRITE")

    anti = cfg.get("anti_overfitting") or {}
    forbidden = [str(x) for x in anti.get("forbidden_core_tokens") or []]
    for rel in anti.get("core_paths") or []:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden:
            if token in text:
                add(errors, "P0X-007", f"pilot-specific token found in core: {rel}: {token}")

    command_path = root / "sdlc/scripts/execute_command_runtime.py"
    if command_path.exists():
        text = command_path.read_text(encoding="utf-8")
        if "build_plan" not in text or "invoke_request" not in text:
            add(errors, "P0X-008", "command runtime must compose routing and invocation layers")

    p02 = root / "sdlc/config/canonical-publish.yaml"
    if p02.exists():
        text = p02.read_text(encoding="utf-8")
        if "CONFIRMED" not in text or "publish" not in text.lower():
            add(errors, "P0X-009", "canonical publish gate does not expose confirmed publish semantics")

    result = {
        "schema_version": 1,
        "artifact_type": "P0_EXIT_STATUS",
        "p0_exit_status": {
            "state": cfg.get("failure_state", "P0_BASELINE_BLOCKED") if errors else cfg.get("success_state", "P0_BASELINE_READY"),
            "production_ready": False,
            "required_path_count": len(required),
            "missing_path_count": len(missing),
            "error_count": len(errors),
            "sample_or_pilot_required_for_gate": False,
            "external_non_p0_blockers": list(cfg.get("external_non_p0_blockers") or []),
            "errors": errors,
        },
    }
    return result, errors


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--gate", type=Path, default=Path("sdlc/config/p0-exit-gate.yaml"))
    p.add_argument("-o", "--output", type=Path)
    a = p.parse_args()
    gate_path = a.gate if a.gate.is_absolute() else a.root / a.gate
    try:
        result, errors = validate(a.root.resolve(), load(gate_path))
    except Exception as exc:
        print(f"P0X-LOAD: {exc}")
        return 2
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if a.output:
        a.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
