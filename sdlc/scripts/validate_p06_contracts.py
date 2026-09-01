#!/usr/bin/env python3
"""Deterministic validators for P0.6 provider/runtime contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PROVIDER_TYPES = {"SOURCE", "TEST", "CANONICAL_REGISTRY", "COMMAND_ROUTER"}
MODES = {"AUTO", "GREENFIELD", "BROWNFIELD", "HYBRID"}
WRITE_MODES = {"READ_ONLY", "READ_WRITE"}
RESPONSE_STATUSES = {"OK", "PARTIAL", "BLOCKED", "ERROR"}
TRUTH = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
CAPABILITY = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*){1,}$")


def add(errors: list[str], code: str, message: str) -> None:
    errors.append(f"{code}: {message}")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def registry_root(data: dict[str, Any]) -> dict[str, Any]:
    return (data or {}).get("registry") or {}


def provider_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p.get("provider_id"): p for p in registry_root(data).get("providers") or [] if p.get("provider_id")}


def validate_registry(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root = registry_root(data)
    if not root:
        return ["P06-001: registry is required"]
    providers = root.get("providers") or []
    if not providers:
        add(errors, "P06-002", "at least one provider is required")
        return errors
    seen: set[str] = set()
    for i, provider in enumerate(providers):
        pid = provider.get("provider_id")
        if not pid:
            add(errors, "P06-003", f"providers[{i}].provider_id is required")
        elif pid in seen:
            add(errors, "P06-004", f"duplicate provider_id: {pid}")
        else:
            seen.add(pid)
        if provider.get("provider_type") not in PROVIDER_TYPES:
            add(errors, "P06-005", f"providers[{i}].provider_type is invalid")
        if provider.get("mode") not in WRITE_MODES:
            add(errors, "P06-006", f"providers[{i}].mode is invalid")
        capabilities = provider.get("capabilities") or []
        if len(capabilities) != len(set(capabilities)):
            add(errors, "P06-007", f"providers[{i}] has duplicate capabilities")
        for capability in capabilities:
            if not CAPABILITY.match(str(capability)):
                add(errors, "P06-008", f"invalid capability name: {capability}")
        for mode in (provider.get("required_for_modes") or []) + (provider.get("optional_for_modes") or []):
            if mode not in MODES:
                add(errors, "P06-009", f"providers[{i}] has invalid project mode: {mode}")
    return errors


def validate_request(data: dict[str, Any], registry: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    req = (data or {}).get("provider_request")
    if not isinstance(req, dict):
        return ["P06-020: provider_request is required"]
    for key in ("request_id", "provider_type", "operation", "project_context", "target"):
        if req.get(key) in (None, "", {}):
            add(errors, "P06-021", f"provider_request.{key} is required")
    if req.get("provider_type") not in PROVIDER_TYPES:
        add(errors, "P06-022", "provider_type is invalid")
    if not CAPABILITY.match(str(req.get("operation", ""))):
        add(errors, "P06-023", "operation must use capability naming")
    context = req.get("project_context") or {}
    if context.get("mode") not in MODES:
        add(errors, "P06-024", "project_context.mode is invalid")
    target = req.get("target") or {}
    if not target.get("target_type") or not target.get("target_id"):
        add(errors, "P06-025", "target_type and target_id are required")
    if req.get("write_intent") is True:
        for key in ("expected_revision", "idempotency_key", "permission_proof_ref"):
            if not req.get(key):
                add(errors, "P06-026", f"write request requires {key}")
    if not isinstance(req.get("extensions", {}), dict):
        add(errors, "P06-027", "extensions must be an object")
    if registry:
        candidates = [p for p in registry_root(registry).get("providers") or []
                      if p.get("enabled") is True
                      and p.get("provider_type") == req.get("provider_type")
                      and req.get("operation") in (p.get("capabilities") or [])]
        if not candidates:
            add(errors, "P06-028", "no enabled provider advertises requested capability")
        if req.get("write_intent") is True and candidates and not any(p.get("mode") == "READ_WRITE" for p in candidates):
            add(errors, "P06-029", "write intent requires READ_WRITE provider")
    return errors


def validate_response(data: dict[str, Any], request: dict[str, Any] | None = None,
                      registry: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    res = (data or {}).get("provider_response")
    if not isinstance(res, dict):
        return ["P06-040: provider_response is required"]
    for key in ("request_id", "provider_id", "provider_type", "operation", "status", "provider_revision"):
        if not res.get(key):
            add(errors, "P06-041", f"provider_response.{key} is required")
    if res.get("provider_type") not in PROVIDER_TYPES:
        add(errors, "P06-042", "response provider_type is invalid")
    if res.get("status") not in RESPONSE_STATUSES:
        add(errors, "P06-043", "response status is invalid")
    if res.get("status") in {"BLOCKED", "ERROR"} and not (res.get("open_items") or res.get("warnings")):
        add(errors, "P06-044", "BLOCKED/ERROR response needs open_items or warnings")
    for i, ev in enumerate(res.get("evidence") or []):
        for key in ("evidence_id", "truth", "locator", "revision"):
            if not ev.get(key):
                add(errors, "P06-045", f"evidence[{i}].{key} is required")
        if ev.get("truth") not in TRUTH:
            add(errors, "P06-046", f"evidence[{i}].truth is invalid")
        if res.get("provider_type") in {"SOURCE", "TEST"} and ev.get("truth") == "CONFIRMED":
            add(errors, "P06-047", "SOURCE/TEST provider evidence must not promote business truth to CONFIRMED")
    if not isinstance(res.get("extensions", {}), dict):
        add(errors, "P06-048", "extensions must be an object")
    if request:
        req = (request or {}).get("provider_request") or {}
        if res.get("request_id") != req.get("request_id"):
            add(errors, "P06-049", "request_id correlation mismatch")
        if res.get("provider_type") != req.get("provider_type"):
            add(errors, "P06-050", "provider_type correlation mismatch")
        if res.get("operation") != req.get("operation"):
            add(errors, "P06-051", "operation correlation mismatch")
    if registry:
        index = provider_index(registry)
        provider = index.get(res.get("provider_id"))
        if not provider:
            add(errors, "P06-052", "response provider_id not found in registry")
        else:
            if provider.get("provider_type") != res.get("provider_type"):
                add(errors, "P06-053", "registry provider_type mismatch")
            if res.get("operation") not in (provider.get("capabilities") or []):
                add(errors, "P06-054", "provider did not advertise response operation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["registry", "request", "response"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()
    try:
        data = load_yaml(args.path)
        registry = load_yaml(args.registry) if args.registry else None
        request = load_yaml(args.request) if args.request else None
    except Exception as exc:
        print(f"P06-LOAD: {exc}", file=sys.stderr)
        return 2
    if args.kind == "registry":
        errors = validate_registry(data)
    elif args.kind == "request":
        errors = validate_request(data, registry)
    else:
        errors = validate_response(data, request, registry)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: P0.6 {args.kind} contract valid: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
