#!/usr/bin/env python3
"""Deterministic /check runtime using the single project configuration entry point."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = _load("check_apply", SCRIPT_DIR / "apply_canonical_delta.py")
CONFIG = _load("check_config", SCRIPT_DIR / "runtime_config.py")
WORK = _load("check_work", SCRIPT_DIR / "run_work.py")

OPEN_WORDS = {"OPEN", "CHECK_REQUIRED", "CONFLICT", "PARTIAL", "CANDIDATE", "ASSUMED", "INFERRED"}


def _legacy_provider(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _open_values(value: Any, prefix: str = "") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(_open_values(child, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            rows.extend(_open_values(child, f"{prefix}[{i}]"))
    elif isinstance(value, str) and any(word in value.upper() for word in OPEN_WORDS):
        rows.append({"path": prefix, "value": value})
    return rows


def _latest_reverse(root: Path) -> dict[str, Any] | None:
    reverse_root = root / "sdlc/runtime/reverse"
    if not reverse_root.exists():
        return None
    candidates = sorted((p for p in reverse_root.rglob("*.json") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if any(key in data for key in ["reverse_candidates", "direct_impacts", "candidate_updates", "summary"]):
            return {"path": path.relative_to(root).as_posix(), "data": data}
    return None


def check(root: Path, *, target_id: str | None = None, setup_only: bool = False) -> dict[str, Any]:
    root = root.resolve()
    provider_path = root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH
    store_path = root / "sdlc/canonical/store.json"
    setup_result = root / "sdlc/runtime/setup/setup-result.json"
    resolved = CONFIG.resolve_runtime_config(root)
    project = resolved["project"]
    project_profile = resolved["project_profile"]
    source_profile = resolved["source_profile"]
    legacy_provider = _legacy_provider(provider_path)
    agent_runtime = CONFIG.resolve_agent_runtime(project, legacy_provider=legacy_provider) if project else {
        "execution_mode": "INTERACTIVE", "ready": False, "provider_required": False, "config_source": "UNCONFIGURED"
    }
    CONFIG.materialize_effective_profiles(root, resolved, provider_config_path=provider_path) if resolved["source_kind"] != "UNCONFIGURED" else None
    git = WORK.git_metadata(root)
    policy = CONFIG.delivery_policy(project_profile) if project_profile else None
    config_ok = resolved["source_kind"] != "UNCONFIGURED"
    execution_ready = bool(config_ok and agent_runtime.get("ready"))

    provider_view = agent_runtime.get("provider_config") or {}
    base = {
        "schema_version": 3,
        "status": "READY" if execution_ready else "SETUP_OR_AGENT_EXECUTION_REQUIRED",
        "setup": {
            "project_config": (root / CONFIG.PROJECT_ENTRY_PATH).is_file(),
            "config_source": resolved["source_kind"],
            "user_config": CONFIG.PROJECT_ENTRY_PATH,
            "project_profile": (root / CONFIG.LEGACY_PROJECT_PROFILE_PATH).is_file(),
            "source_profile": (root / CONFIG.LEGACY_SOURCE_PROFILE_PATH).is_file(),
            "legacy_profiles_role": "MACHINE_GENERATED_OR_LEGACY_FALLBACK",
            "agent_execution": {
                "mode": agent_runtime.get("execution_mode"),
                "ready": agent_runtime.get("ready"),
                "config_source": agent_runtime.get("config_source"),
                "provider_required": agent_runtime.get("provider_required"),
                "provider_id": agent_runtime.get("provider_id"),
                "deprecation": agent_runtime.get("deprecation"),
            },
            "provider": {
                "required": agent_runtime.get("provider_required"),
                "enabled": bool(provider_view.get("enabled")),
                "provider_id": provider_view.get("provider_id"),
                "provider_class": provider_view.get("provider_class"),
            },
            "canonical_store": store_path.is_file(),
            "last_setup_result": setup_result.relative_to(root).as_posix() if setup_result.is_file() else None,
        },
        "project": {
            "name": CONFIG.nested(project, "project", "name", default=None) if project else None,
            "mode": CONFIG.project_mode(project) if project else "UNCONFIGURED",
            "delivery_profile": policy.get("profile") if policy else "UNCONFIGURED",
            "enabled_stages": policy.get("enabled_stages") if policy else [],
            "source_write_roots": CONFIG.source_roots(source_profile),
            "build_commands": CONFIG.build_commands(project),
            "test_commands": CONFIG.test_commands(project),
            "language": CONFIG.nested(project, "technology", "language", default=None),
            "framework": CONFIG.nested(project, "technology", "framework", default=None),
            "database": CONFIG.nested(project, "data", "database", default=None),
            "document_language": CONFIG.nested(project, "documents", "language", default=None),
            "unresolved": CONFIG.nested(project, "unresolved", default=[]),
        },
        "config_usage": resolved["usage"],
        "git": {**git, "dirty_paths": sorted(WORK.git_changed_paths(root)) if git.get("available") else []},
    }
    if setup_only:
        return base

    store = APPLY.load_store(store_path)
    base["canonical"] = {
        "revision": store["revision"],
        "entity_count": len(store.get("entities", {})),
        "relation_count": len(store.get("relations", [])),
    }
    if target_id:
        entity = store.get("entities", {}).get(target_id)
        if not entity:
            base["target"] = {"id": target_id, "found": False}
        else:
            latest = WORK._latest_target_stage(entity)
            related = WORK._related_entity_ids(store, target_id, int(policy.get("graph_hops", 4) if policy else 4))
            base["target"] = {
                "id": target_id,
                "found": True,
                "entity_type": entity.get("entity_type"),
                "truth_status": entity.get("truth_status"),
                "latest_stage": latest,
                "next_stage": WORK._next_stage(latest, policy.get("enabled_stages") if policy else None) if latest else None,
                "open_or_check_required": _open_values(entity),
                "related_entity_count": len(related),
                "provenance_count": len(entity.get("provenance", [])),
            }
    reverse = _latest_reverse(root)
    if reverse:
        data = reverse["data"]
        base["reverse"] = {
            "path": reverse["path"],
            "reverse_candidate_count": len(data.get("reverse_candidates", data.get("candidate_updates", [])) or []),
            "coverage_gaps": data.get("coverage_gaps", []),
            "review_required": bool(data.get("review_required") or data.get("reverse_candidates") or data.get("candidate_updates")),
        }
    return base


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Show Harness/project/target status from .sdlc/project.yaml.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target")
    ap.add_argument("--setup", action="store_true", help="Only check project/agent execution readiness")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    try:
        result = check(Path(args.root), target_id=args.target, setup_only=args.setup)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "CHECK_FAILED", "error": str(exc)}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("status") == "READY" else 4 if result.get("status") == "SETUP_OR_AGENT_EXECUTION_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
