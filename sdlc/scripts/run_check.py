#!/usr/bin/env python3
"""Deterministic /check runtime.

/check must not depend on an Agent to answer basic operational questions. It reports the
current Canonical revision, project/provider readiness, target progress, OPEN-like states,
Source evidence coverage and latest reverse candidates. Semantic recommendations can still
be added by an Agent, but the core status is machine-derived.
"""
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


def _provider(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"configured": False, "enabled": False, "reason": "PROVIDER_CONFIG_MISSING"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"configured": False, "enabled": False, "reason": "PROVIDER_CONFIG_INVALID"}
    command = data.get("command")
    return {
        "configured": True,
        "enabled": bool(data.get("enabled") and isinstance(command, list) and command),
        "provider_id": data.get("provider_id"),
        "provider_class": data.get("provider_class"),
    }


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
    project_path = root / "sdlc/config/project-profile.yaml"
    source_path = root / "sdlc/config/source-profile.yaml"
    provider_path = root / "sdlc/config/agent-provider.json"
    store_path = root / "sdlc/canonical/store.json"
    project = CONFIG.load_config(project_path)
    source = CONFIG.load_config(source_path)
    provider = _provider(provider_path)
    git = WORK.git_metadata(root)
    setup_result = root / "sdlc/runtime/setup/setup-result.json"
    policy = CONFIG.delivery_policy(project) if project else None

    base = {
        "schema_version": 1,
        "status": "READY" if project_path.is_file() and source_path.is_file() and provider["enabled"] else "SETUP_OR_PROVIDER_REQUIRED",
        "setup": {
            "project_profile": project_path.is_file(),
            "source_profile": source_path.is_file(),
            "provider": provider,
            "canonical_store": store_path.is_file(),
            "last_setup_result": setup_result.relative_to(root).as_posix() if setup_result.is_file() else None,
        },
        "project": {
            "mode": CONFIG.project_mode(project) if project else "UNCONFIGURED",
            "delivery_profile": policy.get("profile") if policy else "UNCONFIGURED",
            "enabled_stages": policy.get("enabled_stages") if policy else [],
            "source_write_roots": CONFIG.source_roots(source),
        },
        "git": {**git, "dirty_paths": sorted(WORK.git_changed_paths(root)) if git.get("available") else []},
    }
    if setup_only:
        return base

    store = APPLY.load_store(store_path)
    base["canonical"] = {
        "revision": store["revision"], "entity_count": len(store.get("entities", {})), "relation_count": len(store.get("relations", [])),
    }
    if target_id:
        entity = store.get("entities", {}).get(target_id)
        if not entity:
            base["target"] = {"id": target_id, "found": False}
        else:
            latest = WORK._latest_target_stage(entity)
            related = WORK._related_entity_ids(store, target_id, int(policy.get("graph_hops", 4) if policy else 4))
            base["target"] = {
                "id": target_id, "found": True, "entity_type": entity.get("entity_type"), "truth_status": entity.get("truth_status"),
                "latest_stage": latest, "next_stage": WORK._next_stage(latest, policy.get("enabled_stages") if policy else None) if latest else None,
                "open_or_check_required": _open_values(entity), "related_entity_count": len(related),
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
    ap = argparse.ArgumentParser(description="Show executable Harness/project/target status.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target")
    ap.add_argument("--setup", action="store_true", help="Only check bootstrap/provider readiness")
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
    return 0 if result.get("status") == "READY" else 4 if result.get("status") == "SETUP_OR_PROVIDER_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
