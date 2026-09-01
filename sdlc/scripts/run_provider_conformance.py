#!/usr/bin/env python3
"""Run adapter-neutral P0.7 provider conformance cases."""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_p06_contracts import validate_registry, validate_request, validate_response  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def substitute(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, str):
        for key, replacement in variables.items():
            value = value.replace("${" + key + "}", replacement)
        return value
    if isinstance(value, list):
        return [substitute(x, variables) for x in value]
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    return value


def get_path(data: Any, dotted: str) -> Any:
    current = data
    for part in dotted.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(dotted)
            current = current[part]
        else:
            raise KeyError(dotted)
    return current


def build_registry(descriptor: dict[str, Any]) -> dict[str, Any]:
    return {
        "registry": {
            "protocol_version": "P0.7-conformance",
            "providers": [{
                "provider_id": descriptor.get("provider_id"),
                "provider_type": descriptor.get("provider_type"),
                "provider_state": descriptor.get("provider_state"),
                "enabled": True,
                "mode": descriptor.get("mode"),
                "capabilities": descriptor.get("capabilities") or [],
            }],
        }
    }


def validate_descriptor(descriptor: dict[str, Any]) -> list[str]:
    errors = []
    for key in ("provider_id", "provider_type", "provider_state", "mode", "capabilities", "adapter_version"):
        if descriptor.get(key) in (None, "", []):
            errors.append(f"CONF-001: descriptor.{key} is required")
    registry_errors = validate_registry(build_registry(descriptor)) if not errors else []
    return errors + registry_errors


def assert_expectations(case_id: str, response: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, wanted in (expected.get("equals") or {}).items():
        try:
            actual = get_path(response, path)
        except (KeyError, IndexError, ValueError):
            errors.append(f"{case_id}: missing expected path {path}")
            continue
        if actual != wanted:
            errors.append(f"{case_id}: {path} expected {wanted!r}, got {actual!r}")
    for path, wanted in (expected.get("contains") or {}).items():
        try:
            actual = get_path(response, path)
        except (KeyError, IndexError, ValueError):
            errors.append(f"{case_id}: missing contains path {path}")
            continue
        if isinstance(actual, (list, str, dict)):
            if wanted not in actual:
                errors.append(f"{case_id}: {path} does not contain {wanted!r}")
        else:
            errors.append(f"{case_id}: {path} is not containable")
    for path, minimum in (expected.get("min_length") or {}).items():
        try:
            actual = get_path(response, path)
            length = len(actual)
        except Exception:
            errors.append(f"{case_id}: cannot measure {path}")
            continue
        if length < int(minimum):
            errors.append(f"{case_id}: {path} length {length} < {minimum}")
    return errors


def run_suite(path: Path) -> tuple[dict[str, Any], list[str]]:
    raw = load(path)
    suite = raw.get("conformance_suite") or {}
    module_name = ((suite.get("adapter") or {}).get("module"))
    if not module_name:
        return {}, ["CONF-000: conformance_suite.adapter.module is required"]
    module = importlib.import_module(module_name)
    if not hasattr(module, "describe") or not hasattr(module, "invoke"):
        return {}, ["CONF-002: adapter must export describe() and invoke()"]
    descriptor = module.describe()
    errors = validate_descriptor(descriptor)
    registry = build_registry(descriptor)

    variables = {
        "SUITE_DIR": str(path.parent.resolve()),
        "REPO_ROOT": str(REPO_ROOT.resolve()),
        "PYTHON": sys.executable,
        "PATH": os.environ.get("PATH", ""),
    }
    adapter_config = substitute((suite.get("adapter") or {}).get("config") or {}, variables)
    case_results = []
    advertised = set(descriptor.get("capabilities") or [])

    for case in suite.get("cases") or []:
        case_id = str(case.get("case_id") or "UNNAMED")
        request = substitute(case.get("request") or {}, variables)
        req = request.get("provider_request") or request
        schema_errors = validate_request(request, None)
        if schema_errors:
            errors.extend(f"{case_id}: {e}" for e in schema_errors)
            continue
        try:
            response = module.invoke(request, adapter_config)
        except Exception as exc:
            errors.append(f"{case_id}: adapter raised exception: {exc}")
            continue
        operation = req.get("operation")
        response_errors = validate_response(response, request, registry if operation in advertised else None)
        errors.extend(f"{case_id}: {e}" for e in response_errors)
        errors.extend(assert_expectations(case_id, response, case.get("expected") or {}))
        case_results.append({
            "case_id": case_id,
            "operation": operation,
            "provider_status": (response.get("provider_response") or {}).get("status"),
            "retryable": bool((response.get("provider_response") or {}).get("retryable")),
            "passed": not any(e.startswith(case_id + ":") for e in errors),
        })

    result = {
        "schema_version": 1,
        "artifact_type": "PROVIDER_CONFORMANCE_RESULT",
        "suite_id": suite.get("suite_id"),
        "adapter_descriptor": descriptor,
        "case_results": case_results,
        "summary": {
            "case_count": len(case_results),
            "passed_count": sum(1 for x in case_results if x["passed"]),
            "failed_count": sum(1 for x in case_results if not x["passed"]),
            "status": "PASS" if not errors else "FAIL",
        },
    }
    return result, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    try:
        result, errors = run_suite(args.suite)
    except Exception as exc:
        print(f"CONF-LOAD: {exc}", file=sys.stderr)
        return 2
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
