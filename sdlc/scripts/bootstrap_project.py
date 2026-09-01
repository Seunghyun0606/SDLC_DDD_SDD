#!/usr/bin/env python3
"""Bounded Greenfield/Brownfield bootstrap without inventing project truth."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any
import yaml

USABLE_PROVIDER_STATES = {"AVAILABLE", "DEGRADED"}


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stable_project_id(name: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").upper()
    return token or "PROJECT-UNASSIGNED"


def exists_bounded(root: Path, candidate: str, max_depth: int) -> bool:
    direct = root / candidate
    if direct.exists():
        return True
    if max_depth < 2:
        return False
    for child in root.iterdir() if root.exists() else []:
        if child.is_dir() and (child / candidate).exists():
            return True
    return False


def discover_markers(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    boot = config.get("bootstrap") or {}
    scan = boot.get("scan_policy") or {}
    max_depth = int(scan.get("max_depth", 2))
    markers = boot.get("brownfield_markers") or {}
    found = []
    for kind, candidates in markers.items():
        for candidate in candidates or []:
            if exists_bounded(root, candidate, max_depth):
                found.append({"asset_type": kind.upper(), "locator": candidate, "truth_state": "OBSERVED"})
    for candidate in boot.get("document_candidates") or []:
        if exists_bounded(root, candidate, max_depth):
            found.append({"asset_type": "DOCUMENT_CANDIDATE", "locator": candidate, "truth_state": "OBSERVED"})
    for candidate in boot.get("data_candidates") or []:
        if exists_bounded(root, candidate, max_depth):
            found.append({"asset_type": "DATA_CANDIDATE", "locator": candidate, "truth_state": "OBSERVED"})
    return found


def provider_states(registry: dict[str, Any]) -> dict[str, str]:
    result = {}
    for provider in ((registry.get("registry") or {}).get("providers") or []):
        result[str(provider.get("provider_type"))] = str(provider.get("provider_state") or "UNKNOWN")
    return result


def bootstrap(project_root: Path, profile: dict[str, Any], registry: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    project = profile.get("project") or {}
    name = str(project.get("name") or project_root.name or "project")
    project_id = str(project.get("id") or stable_project_id(name))
    requested_mode = str(project.get("mode") or "AUTO")
    markers = discover_markers(project_root, config)
    if requested_mode == "AUTO":
        resolved_mode = "BROWNFIELD" if markers else "GREENFIELD"
        mode_truth = "OBSERVED"
    else:
        resolved_mode = requested_mode
        mode_truth = "GIVEN"

    states = provider_states(registry)
    source_state = states.get("SOURCE", "UNCONFIGURED")
    test_state = states.get("TEST", "UNCONFIGURED")
    open_items = []
    decisions = []

    if resolved_mode == "GREENFIELD":
        for key in config.get("greenfield_decisions") or []:
            decisions.append({"decision_key": key, "state": "OPEN", "candidate": None, "confirmed_value": None})
            open_items.append({
                "open_id": f"OPEN-DECISION-{key.upper()}",
                "type": "GREENFIELD_DECISION",
                "question": f"{key} 값을 결정해야 하는가?",
                "blocks_reasoning": False,
                "blocks_action": False,
                "action_scopes": [],
                "escalation": "ARCHITECT_OR_ENGINEERING_OWNER",
            })
    elif source_state not in USABLE_PROVIDER_STATES:
        open_items.append({
            "open_id": "OPEN-SOURCE-PROVIDER",
            "type": "PROVIDER_CAPABILITY",
            "question": "Brownfield Source claim을 위해 Source Provider를 연결할 수 있는가?",
            "blocks_reasoning": False,
            "blocks_action": True,
            "action_scopes": ["source.snapshot.read", "source.search", "source.object.read", "source.diff", "source.write"],
            "escalation": "ENGINEERING_OWNER",
        })

    artifact_profile = ((profile.get("artifacts") or {}).get("profile")) or "STANDARD"
    first_work_allowed = bool(project_id and resolved_mode and states)
    source_claim_allowed = resolved_mode == "GREENFIELD" or source_state in USABLE_PROVIDER_STATES

    return {
        "schema_version": 1,
        "artifact_type": "PROJECT_BOOTSTRAP_RESULT",
        "project_bootstrap": {
            "project_id": project_id,
            "project_name": name,
            "requested_mode": requested_mode,
            "resolved_mode": resolved_mode,
            "mode_truth": mode_truth,
            "artifact_profile": artifact_profile,
            "project_root": str(project_root),
            "scan_policy": {
                "bounded": True,
                "max_depth": int(((config.get("bootstrap") or {}).get("scan_policy") or {}).get("max_depth", 2)),
                "unlimited_recursive_scan": False,
            },
            "provider_states": states,
            "assets": markers,
            "technology_decisions": decisions,
            "open_items": open_items,
            "entry_gate": {
                "first_work_allowed": first_work_allowed,
                "source_claim_allowed": source_claim_allowed,
                "source_provider_state": source_state,
                "test_provider_state": test_state,
                "warnings": [x.get("open_id") for x in open_items],
            },
            "next": {
                "human_decisions_required_now": False,
                "recommended_command": "/work",
                "first_stage": "INTAKE",
                "do_not_auto_confirm_open_decisions": True,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("project_profile", type=Path)
    parser.add_argument("provider_registry", type=Path)
    parser.add_argument("--config", type=Path, default=Path("sdlc/config/bootstrap-runtime.yaml"))
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = bootstrap(args.project_root, load(args.project_profile), load(args.provider_registry), load(args.config))
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
