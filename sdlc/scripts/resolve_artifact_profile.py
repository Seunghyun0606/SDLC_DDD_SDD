#!/usr/bin/env python3
"""Resolve LITE/STANDARD/ENTERPRISE into an executable artifact plan."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml

ENABLED_VALUES = {"MUST", "OPTIONAL", "CONDITIONAL", "CONDITIONAL_L2_ONLY", "CONFIGURABLE_L1_L2"}
DISABLED_VALUES = {"OFF", "DISABLED", False, None}


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve(profile_config: dict[str, Any], project_profile: dict[str, Any], explicit_profile: str | None = None) -> dict[str, Any]:
    resolver = profile_config.get("resolver") or {}
    selected = explicit_profile or ((project_profile.get("artifacts") or {}).get("profile")) or resolver.get("default_profile") or "STANDARD"
    profiles = profile_config.get("profiles") or {}
    if selected not in profiles:
        raise ValueError(f"unknown artifact profile: {selected}")

    selected_doc = profiles[selected] or {}
    human = selected_doc.get("human_artifacts") or {}
    enabled = []
    disabled = []
    conditional = []
    for artifact, rule in human.items():
        if rule in DISABLED_VALUES:
            disabled.append(artifact)
        elif rule == "MUST":
            enabled.append(artifact)
        elif rule in ENABLED_VALUES:
            conditional.append({"artifact": artifact, "rule": rule})
        else:
            conditional.append({"artifact": artifact, "rule": str(rule)})

    return {
        "schema_version": 1,
        "artifact_type": "RESOLVED_ARTIFACT_PROFILE",
        "profile": selected,
        "description": selected_doc.get("description"),
        "human_artifacts": human,
        "enabled_required": enabled,
        "conditional": conditional,
        "disabled": disabled,
        "internal_capabilities": selected_doc.get("internal_capabilities") or {},
        "invariants": profile_config.get("invariants") or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile_config", type=Path)
    parser.add_argument("project_profile", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = resolve(load(args.profile_config), load(args.project_profile), args.profile)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
