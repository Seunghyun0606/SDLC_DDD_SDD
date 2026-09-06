#!/usr/bin/env python3
"""v1.9 project-config compatibility layer for the Tailoring / Human Control Plane.

The v1.8 runtime remains the execution core. This module extends the single human entry
``.sdlc/project.yaml`` with Change Level and Artifact Profile keys without weakening the
fail-closed DEAD_CONFIG rule.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("runtime_config_v18_base", HERE / "runtime_config.py")
BASE = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(BASE)

PROJECT_ENTRY_PATH = BASE.PROJECT_ENTRY_PATH
LEGACY_PROJECT_PROFILE_PATH = BASE.LEGACY_PROJECT_PROFILE_PATH
LEGACY_SOURCE_PROFILE_PATH = BASE.LEGACY_SOURCE_PROFILE_PATH
DEFAULT_PROVIDER_CONFIG_PATH = BASE.DEFAULT_PROVIDER_CONFIG_PATH
EFFECTIVE_DIR = BASE.EFFECTIVE_DIR
DELIVERY_PROFILES = BASE.DELIVERY_PROFILES
AGENT_EXECUTION_MODES = BASE.AGENT_EXECUTION_MODES

load_yaml_subset = BASE.load_yaml_subset
load_config = BASE.load_config
nested = BASE.nested
project_mode = BASE.project_mode
delivery_profile = BASE.delivery_profile
delivery_policy = BASE.delivery_policy
command_list = BASE.command_list
provider_command = BASE.provider_command
agent_execution_mode = BASE.agent_execution_mode
resolve_agent_runtime = BASE.resolve_agent_runtime
source_roots = BASE.source_roots
build_commands = BASE.build_commands
test_commands = BASE.test_commands

V19_RUNTIME_PATHS = {
    "change.level_policy",
    "change.default_level",
    "documents.internal.profile",
    "documents.customer.profile",
    "documents.pm.profile",
    "documents.machine.visibility",
}
V19_DOCUMENT_PATHS = {
    "documents.internal.output_root",
    "documents.customer.output_root",
    "documents.pm.output_root",
}


def _flatten_leaves(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        rows: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_leaves(child, child_prefix))
        return rows
    return [prefix] if prefix else []


def classify_project_config(project: dict[str, Any]) -> dict[str, list[str]]:
    """Classify v1.9 keys while preserving v1.8 categories and fail-closed semantics."""
    result = {"runtime": [], "extension": [], "document": [], "dead": []}
    base_runtime = set(BASE.RUNTIME_CONSUMED_PATHS)
    base_doc = set(BASE.DOCUMENT_ONLY_PATHS)
    for path in sorted(set(_flatten_leaves(project))):
        if path in base_runtime or path in V19_RUNTIME_PATHS:
            result["runtime"].append(path)
        elif any(path.startswith(prefix) for prefix in BASE.EXTENSION_PREFIXES):
            result["extension"].append(path)
        elif (
            path in base_doc
            or path in V19_DOCUMENT_PATHS
            or any(path.startswith(prefix) for prefix in BASE.DOCUMENT_CONTEXT_PREFIXES)
        ):
            result["document"].append(path)
        else:
            result["dead"].append(path)
    return result


def _validate_v19(project: dict[str, Any]) -> None:
    policy = str(nested(project, "change", "level_policy", default="AUTO") or "AUTO").upper()
    if policy not in {"AUTO", "MANUAL"}:
        raise ValueError("change.level_policy must be AUTO or MANUAL")
    default_level = nested(project, "change", "default_level", default=None)
    if default_level is not None and str(default_level).upper() not in {"L1", "L2", "L3", "L4", "L5"}:
        raise ValueError("change.default_level must be one of L1..L5")
    for audience in ["internal", "customer", "pm"]:
        profile = nested(project, "documents", audience, "profile", default=None)
        if profile is not None and (not isinstance(profile, str) or not profile.strip()):
            raise ValueError(f"documents.{audience}.profile must be a non-empty profile id")
    visibility = str(nested(project, "documents", "machine", "visibility", default="HIDDEN") or "HIDDEN").upper()
    if visibility not in {"HIDDEN", "DEBUG"}:
        raise ValueError("documents.machine.visibility must be HIDDEN or DEBUG")


def ensure_no_dead_config(project: dict[str, Any]) -> None:
    dead = classify_project_config(project)["dead"]
    if dead:
        raise ValueError("unused project config key(s): " + ", ".join(dead))


def compact_project_context(project: dict[str, Any]) -> dict[str, Any]:
    context = BASE.compact_project_context(project)
    if "change" in project:
        context["change"] = project["change"]
    return context


def project_to_legacy_profiles(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    project_profile, source_profile = BASE.project_to_legacy_profiles(project)
    project_profile["project_context"] = compact_project_context(project)
    return project_profile, source_profile


def resolve_runtime_config(
    root: Path,
    *,
    project_config_path: Path | None = None,
    legacy_project_path: Path | None = None,
    legacy_source_path: Path | None = None,
    validate_usage: bool = True,
) -> dict[str, Any]:
    resolved = BASE.resolve_runtime_config(
        root,
        project_config_path=project_config_path,
        legacy_project_path=legacy_project_path,
        legacy_source_path=legacy_source_path,
        validate_usage=False,
    )
    project = resolved.get("project") or {}
    if resolved.get("source_kind") == "PROJECT_ENTRY":
        _validate_v19(project)
        if validate_usage:
            ensure_no_dead_config(project)
    if project:
        project_profile, source_profile = project_to_legacy_profiles(project)
        resolved["project_profile"] = project_profile
        resolved["source_profile"] = source_profile
        resolved["project_context"] = compact_project_context(project)
        resolved["usage"] = classify_project_config(project)
    return resolved


def materialize_effective_profiles(
    root: Path,
    resolved: dict[str, Any] | None = None,
    *,
    provider_config_path: Path | None = None,
) -> dict[str, Path]:
    root = root.resolve()
    resolved = resolved or resolve_runtime_config(root)
    paths = BASE.materialize_effective_profiles(root, resolved, provider_config_path=provider_config_path)
    effective = root / EFFECTIVE_DIR
    tailoring_path = effective / "tailoring-config.json"
    project = resolved.get("project") or {}
    payload = {
        "schema_version": 1,
        "change": project.get("change", {"level_policy": "AUTO"}),
        "documents": project.get("documents", {}),
        "config_usage": resolved.get("usage", {}),
    }
    tailoring_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["tailoring_config"] = tailoring_path
    return paths
