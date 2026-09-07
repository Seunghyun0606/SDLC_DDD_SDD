#!/usr/bin/env python3
"""Canonical project configuration resolver for SDLC Harness.

Human control-plane settings live in one project entry file. Change Level controls execution depth;
Engineering/Customer profiles independently control Human Artifact topology.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("runtime_config_base", HERE / "runtime_config.py")
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
legacy_to_project = BASE.legacy_to_project

DEFAULT_ENGINEERING_PROFILE = "ENGINEERING_SDD_COMPACT"
DEFAULT_CUSTOMER_PROFILE = "CUSTOMER_STANDARD_3"
DEFAULT_PM_PROFILE = "PM_STANDARD"
LEVELS = {"L1", "L2", "L3", "L4", "L5"}

CONTROL_RUNTIME_PATHS = {
    "change.level_policy",
    "change.default_level",
    "change.minimum_level",
    "documents.engineering.profile",
    "documents.engineering.manual_edit_policy",
    "documents.engineering.freshness",
    "documents.internal.profile",
    "documents.customer.profile",
    "documents.customer.scope",
    "documents.customer.freshness",
    "documents.customer.projection_contract",
    "documents.customer.projection_config",
    "documents.customer.final_review.human_editable",
    "documents.pm.profile",
    "documents.machine.visibility",
}
CONTROL_RUNTIME_PREFIXES = ("change.target_levels.",)
CONTROL_DOCUMENT_PATHS = {
    "documents.engineering.output_root",
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


def normalize_document_profiles(project: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(project)
    documents = normalized.setdefault("documents", {})
    if not isinstance(documents, dict):
        raise ValueError("documents must be a mapping")

    engineering = documents.setdefault("engineering", {})
    internal = documents.setdefault("internal", {})
    customer = documents.setdefault("customer", {})
    pm = documents.setdefault("pm", {})
    machine = documents.setdefault("machine", {})
    for name, value in {
        "documents.engineering": engineering,
        "documents.internal": internal,
        "documents.customer": customer,
        "documents.pm": pm,
        "documents.machine": machine,
    }.items():
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be a mapping")

    engineering_profile = engineering.get("profile")
    internal_profile = internal.get("profile")
    if engineering_profile:
        effective_engineering = str(engineering_profile)
    elif internal_profile:
        effective_engineering = str(internal_profile)
    else:
        effective_engineering = DEFAULT_ENGINEERING_PROFILE

    engineering["profile"] = effective_engineering
    internal["profile"] = effective_engineering
    engineering.setdefault("manual_edit_policy", "TYPO_ONLY")
    engineering.setdefault("freshness", "CANONICAL_REVISION")
    customer.setdefault("profile", DEFAULT_CUSTOMER_PROFILE)
    customer.setdefault("scope", "RQ")
    customer.setdefault("freshness", "CANONICAL_AND_AS_BUILT")
    final_review = customer.setdefault("final_review", {})
    if not isinstance(final_review, dict):
        raise ValueError("documents.customer.final_review must be a mapping")
    final_review.setdefault("human_editable", True)
    pm.setdefault("profile", DEFAULT_PM_PROFILE)
    machine.setdefault("visibility", "HIDDEN")
    return normalized


def classify_project_config(project: dict[str, Any]) -> dict[str, list[str]]:
    result = {"runtime": [], "extension": [], "document": [], "dead": []}
    base_runtime = set(BASE.RUNTIME_CONSUMED_PATHS)
    base_doc = set(BASE.DOCUMENT_ONLY_PATHS)
    for path in sorted(set(_flatten_leaves(project))):
        if path in base_runtime or path in CONTROL_RUNTIME_PATHS or any(path.startswith(p) for p in CONTROL_RUNTIME_PREFIXES):
            result["runtime"].append(path)
        elif any(path.startswith(prefix) for prefix in BASE.EXTENSION_PREFIXES):
            result["extension"].append(path)
        elif path in base_doc or path in CONTROL_DOCUMENT_PATHS or any(path.startswith(prefix) for prefix in BASE.DOCUMENT_CONTEXT_PREFIXES):
            result["document"].append(path)
        else:
            result["dead"].append(path)
    return result


def _valid_level(value: Any, label: str) -> None:
    if value is not None and str(value).upper() not in LEVELS:
        raise ValueError(f"{label} must be one of L1..L5")


def _validate_control_plane(project: dict[str, Any]) -> None:
    policy = str(nested(project, "change", "level_policy", default="AUTO") or "AUTO").upper()
    if policy not in {"AUTO", "MANUAL"}:
        raise ValueError("change.level_policy must be AUTO or MANUAL")
    _valid_level(nested(project, "change", "default_level", default=None), "change.default_level")
    _valid_level(nested(project, "change", "minimum_level", default=None), "change.minimum_level")

    target_levels = nested(project, "change", "target_levels", default={}) or {}
    if not isinstance(target_levels, dict):
        raise ValueError("change.target_levels must be a mapping keyed by target id")
    for target, raw in target_levels.items():
        if not str(target).strip():
            raise ValueError("change.target_levels target id must not be empty")
        if isinstance(raw, str):
            _valid_level(raw, f"change.target_levels.{target}")
            continue
        if not isinstance(raw, dict):
            raise ValueError(f"change.target_levels.{target} must be a level string or mapping")
        unknown = set(raw) - {"level", "reason", "accept_below_safety_floor"}
        if unknown:
            raise ValueError(f"change.target_levels.{target} has unsupported key(s): {', '.join(sorted(unknown))}")
        _valid_level(raw.get("level"), f"change.target_levels.{target}.level")
        if not raw.get("level"):
            raise ValueError(f"change.target_levels.{target}.level is required")
        if raw.get("reason") is not None and (not isinstance(raw.get("reason"), str) or not str(raw.get("reason")).strip()):
            raise ValueError(f"change.target_levels.{target}.reason must be non-empty text")
        if raw.get("accept_below_safety_floor") is not None and not isinstance(raw.get("accept_below_safety_floor"), bool):
            raise ValueError(f"change.target_levels.{target}.accept_below_safety_floor must be boolean")

    for audience in ["engineering", "internal", "customer", "pm"]:
        profile = nested(project, "documents", audience, "profile", default=None)
        if profile is not None and (not isinstance(profile, str) or not profile.strip()):
            raise ValueError(f"documents.{audience}.profile must be a non-empty profile id")

    edit_policy = str(nested(project, "documents", "engineering", "manual_edit_policy", default="TYPO_ONLY") or "TYPO_ONLY").upper()
    if edit_policy not in {"TYPO_ONLY", "READ_ONLY", "HUMAN_REVIEW"}:
        raise ValueError("documents.engineering.manual_edit_policy must be TYPO_ONLY, READ_ONLY, or HUMAN_REVIEW")
    scope = str(nested(project, "documents", "customer", "scope", default="RQ") or "RQ").upper()
    if scope not in {"RQ", "MILESTONE", "PROJECT"}:
        raise ValueError("documents.customer.scope must be RQ, MILESTONE, or PROJECT")
    for key in ["projection_contract", "projection_config"]:
        value = nested(project, "documents", "customer", key, default=None)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"documents.customer.{key} must be a non-empty repository path")
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
    if "documents" in project:
        context["documents"] = project["documents"]
    return context


def project_to_legacy_profiles(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    project_profile, source_profile = BASE.project_to_legacy_profiles(project)
    project_profile["project_context"] = compact_project_context(project)
    return project_profile, source_profile


def resolve_runtime_config(root: Path, *, project_config_path: Path | None = None,
                           legacy_project_path: Path | None = None, legacy_source_path: Path | None = None,
                           validate_usage: bool = True) -> dict[str, Any]:
    resolved = BASE.resolve_runtime_config(
        root, project_config_path=project_config_path, legacy_project_path=legacy_project_path,
        legacy_source_path=legacy_source_path, validate_usage=False,
    )
    raw_project = resolved.get("project") or {}
    if raw_project:
        if resolved.get("source_kind") == "PROJECT_ENTRY":
            _validate_control_plane(raw_project)
            if validate_usage:
                ensure_no_dead_config(raw_project)
        project = normalize_document_profiles(raw_project)
        resolved["project"] = project
        project_profile, source_profile = project_to_legacy_profiles(project)
        resolved["project_profile"] = project_profile
        resolved["source_profile"] = source_profile
        resolved["project_context"] = compact_project_context(project)
        resolved["usage"] = classify_project_config(raw_project)
        resolved["document_profile_resolution"] = {
            "engineering": nested(project, "documents", "engineering", "profile"),
            "legacy_internal_alias": nested(project, "documents", "internal", "profile"),
            "customer": nested(project, "documents", "customer", "profile"),
            "pm": nested(project, "documents", "pm", "profile"),
            "engineering_customer_topology_independent": True,
            "change_level_projection_topology_independent": True,
        }
    return resolved


def materialize_effective_profiles(root: Path, resolved: dict[str, Any] | None = None,
                                   *, provider_config_path: Path | None = None) -> dict[str, Path]:
    root = root.resolve()
    resolved = resolved or resolve_runtime_config(root)
    paths = BASE.materialize_effective_profiles(root, resolved, provider_config_path=provider_config_path)
    effective = root / EFFECTIVE_DIR
    tailoring_path = effective / "tailoring-config.json"
    project = resolved.get("project") or {}
    payload = {
        "schema_version": 3,
        "change": project.get("change", {"level_policy": "AUTO"}),
        "documents": project.get("documents", {}),
        "profile_resolution": resolved.get("document_profile_resolution", {}),
        "config_usage": resolved.get("usage", {}),
    }
    tailoring_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["tailoring_config"] = tailoring_path
    return paths
