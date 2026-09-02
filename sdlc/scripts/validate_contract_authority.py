#!/usr/bin/env python3
"""Validate that one declared primary authority exists for each operational concept."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def validate(repo_root: Path, config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    authorities = config.get("authorities") or {}
    if not authorities:
        return ["P1A-001 authorities required"]
    seen_paths: dict[str, str] = {}
    for concept, spec in authorities.items():
        path = str((spec or {}).get("path") or "")
        if not path:
            errors.append(f"P1A-002 authority path missing: {concept}"); continue
        if path in seen_paths:
            errors.append(f"P1A-003 duplicate primary authority path: {path} ({seen_paths[path]}, {concept})")
        seen_paths[path] = concept
        if not spec.get("generated") and not (repo_root / path).exists():
            errors.append(f"P1A-004 authority path not found: {concept}={path}")
        if (spec or {}).get("kind") not in {"HUMAN_PRIMARY", "RUNTIME_PRIMARY", "MACHINE_PRIMARY", "PROJECT_RUNTIME_PRIMARY"}:
            errors.append(f"P1A-005 invalid authority kind: {concept}")
    for root in config.get("non_authoritative_roots") or []:
        if any(path == root or path.startswith(root.rstrip("/") + "/") for path in seen_paths):
            errors.append(f"P1A-006 primary authority declared under non-authoritative root: {root}")
    return errors


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("config", type=Path); p.add_argument("--repo-root", type=Path, default=Path(".")); args = p.parse_args()
    errors = validate(args.repo_root.resolve(), load(args.config))
    if errors:
        print("\n".join(errors)); return 1
    print("OK: contract authority index valid"); return 0


if __name__ == "__main__": raise SystemExit(main())
