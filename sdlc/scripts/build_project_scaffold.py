#!/usr/bin/env python3
"""Export the actual project-facing SDLC Scaffold from the framework repository.

Framework development history, pilots, validation results, samples and this distribution tool itself
are deliberately excluded from the generated project. Legacy formal profiles/templates can be
opted in only as an explicit compatibility package.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

CONTRACT = "sdlc/design/contracts/project-scaffold-contract.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_files(root: Path, *, include_legacy_compatibility: bool = False) -> list[str]:
    contract = _load(root / CONTRACT)
    package = _load(root / contract["source_package_contract"])
    rows = list(package[contract["base_file_set"]]) + list(contract.get("add_required_files") or [])
    exact = set(contract.get("exclude_exact") or [])
    prefixes = tuple(contract.get("exclude_prefixes") or [])
    framework_tools = set(contract.get("framework_distribution_tools") or [])

    selected: list[str] = []
    for rel in rows:
        if rel in framework_tools:
            continue
        if rel in exact or any(rel.startswith(prefix) for prefix in prefixes):
            continue
        if rel not in selected:
            selected.append(rel)

    if include_legacy_compatibility:
        for rel in contract.get("legacy_compatibility_package") or []:
            if rel not in selected:
                selected.append(rel)
    return selected


def _materialize_compatibility_aliases(output: Path, contract: dict[str, Any]) -> list[dict[str, str]]:
    """Create declared compatibility aliases without maintaining a second source copy.

    Directory symlinks are preferred. On hosts that cannot create them, copytree is a portability
    fallback so legacy Runtime paths remain executable even though the Framework source has one
    canonical template tree.
    """
    materialized: list[dict[str, str]] = []
    for row in contract.get("compatibility_aliases") or []:
        alias_rel = str(row.get("path") or "").strip()
        target_raw = str(row.get("target") or "").strip()
        if not alias_rel or not target_raw:
            raise ValueError("compatibility alias requires path and target")
        alias = output / alias_rel
        target = alias.parent / target_raw
        if not target.exists():
            raise ValueError(f"compatibility alias target missing: {target.relative_to(output).as_posix()}")
        alias.parent.mkdir(parents=True, exist_ok=True)
        if alias.exists() or alias.is_symlink():
            raise ValueError(f"compatibility alias path already exists: {alias_rel}")
        mode = "SYMLINK"
        try:
            alias.symlink_to(target_raw, target_is_directory=target.is_dir())
        except (OSError, NotImplementedError):
            if target.is_dir():
                shutil.copytree(target, alias)
            else:
                shutil.copy2(target, alias)
            mode = "COPY_FALLBACK"
        materialized.append({"path": alias_rel, "target": target_raw, "mode": mode})
    return materialized


def build(root: Path, output: Path, *, include_legacy_compatibility: bool = False) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError("project scaffold output must be outside framework repository")

    contract = _load(root / CONTRACT)
    files = select_files(root, include_legacy_compatibility=include_legacy_compatibility)
    missing = [rel for rel in files if not (root / rel).is_file()]
    if missing:
        raise ValueError("scaffold source file missing: " + ", ".join(missing[:10]))

    for rel in files:
        dst = output / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dst)

    aliases = _materialize_compatibility_aliases(output, contract)
    alias_paths = {str(row["path"]).rstrip("/") for row in aliases}

    compatibility = set(contract.get("legacy_compatibility_package") or []) if include_legacy_compatibility else set()
    forbidden_present: list[str] = []
    for prefix in contract.get("exclude_prefixes") or []:
        normalized = prefix.rstrip("/")
        if normalized in alias_paths:
            continue
        path = output / normalized
        if not path.exists():
            continue
        allowed_here = [rel for rel in compatibility if rel.startswith(prefix)]
        actual_files = [p.relative_to(output).as_posix() for p in path.rglob("*") if p.is_file()]
        if any(rel not in allowed_here for rel in actual_files):
            forbidden_present.append(prefix)

    for rel in contract.get("framework_distribution_tools") or []:
        if (output / rel).exists():
            forbidden_present.append(rel)

    return {
        "status": "PROJECT_SCAFFOLD_BUILT",
        "file_count": len(files),
        "output": str(output),
        "default_engineering_profile": contract["default_engineering_profile"],
        "default_internal_profile": contract["default_internal_profile"],
        "default_customer_profile": contract["default_customer_profile"],
        "legacy_compatibility_included": include_legacy_compatibility,
        "compatibility_aliases": aliases,
        "forbidden_framework_dev_assets_present": sorted(set(forbidden_present)),
        "framework_distribution_tools_included": False,
        "stage_oriented_full_default": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", required=True)
    ap.add_argument("--include-legacy-compatibility", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = build(
            Path(args.root),
            Path(args.output),
            include_legacy_compatibility=args.include_legacy_compatibility,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
