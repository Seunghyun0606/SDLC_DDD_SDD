#!/usr/bin/env python3
"""Export the actual project-facing SDLC Scaffold from the framework repository.

Framework development history, pilots, validation results and samples are deliberately excluded.
Legacy STAGE_ORIENTED_FULL can be opted in only as a compatibility package.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

CONTRACT = "sdlc/design/contracts/project-scaffold-contract.json"


def _load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8"))


def select_files(root: Path, *, include_legacy_compatibility: bool = False) -> list[str]:
    contract = _load(root / CONTRACT); package = _load(root / contract["source_package_contract"])
    rows = list(package[contract["base_file_set"]]) + list(contract.get("add_required_files") or [])
    exact = set(contract.get("exclude_exact") or []); prefixes = tuple(contract.get("exclude_prefixes") or [])
    selected = []
    for rel in rows:
        if rel in exact or any(rel.startswith(prefix) for prefix in prefixes): continue
        if rel not in selected: selected.append(rel)
    if include_legacy_compatibility:
        for rel in contract.get("legacy_compatibility_package") or []:
            if rel not in selected: selected.append(rel)
    return selected


def build(root: Path, output: Path, *, include_legacy_compatibility: bool = False) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError("project scaffold output must be outside framework repository")
    files = select_files(root, include_legacy_compatibility=include_legacy_compatibility)
    missing = [rel for rel in files if not (root / rel).is_file()]
    if missing: raise ValueError("scaffold source file missing: " + ", ".join(missing[:10]))
    for rel in files:
        dst = output / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(root / rel, dst)
    contract = _load(root / CONTRACT)
    forbidden_present = []
    for prefix in contract.get("exclude_prefixes") or []:
        if (output / prefix.rstrip("/")).exists(): forbidden_present.append(prefix)
    return {
        "status": "PROJECT_SCAFFOLD_BUILT",
        "file_count": len(files),
        "output": str(output),
        "default_internal_profile": contract["default_internal_profile"],
        "legacy_compatibility_included": include_legacy_compatibility,
        "forbidden_framework_dev_assets_present": forbidden_present,
        "stage_oriented_full_default": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--output", required=True); ap.add_argument("--include-legacy-compatibility", action="store_true"); args = ap.parse_args(argv)
    try:
        result = build(Path(args.root), Path(args.output), include_legacy_compatibility=args.include_legacy_compatibility); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
