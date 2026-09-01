#!/usr/bin/env python3
"""Generic bounded repository inventory used before language/framework-specific analyzers."""
from __future__ import annotations

import argparse
import hashlib
import os
from collections import Counter
from pathlib import Path
from typing import Any
import yaml

DEFAULT_EXCLUDES = {".git", ".idea", ".vscode", "node_modules", "dist", "build", "target", ".venv", "venv", "__pycache__"}
BUILD_MARKERS = {"pom.xml", "build.gradle", "build.gradle.kts", "package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml"}
TEST_MARKERS = {"pytest.ini", "tox.ini", "jest.config.js", "jest.config.ts", "vitest.config.ts", "build.gradle", "pom.xml"}
DATA_NAMES = {"db", "database", "migrations", "schema", "sql"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def depth(root: Path, current: Path) -> int:
    try:
        return len(current.relative_to(root).parts)
    except ValueError:
        return 999


def inventory(root: Path, source_revision: str, max_depth: int = 4, max_files: int = 5000) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError(f"source_root is not a directory: {root}")
    extensions: Counter[str] = Counter()
    build_files = []
    test_files = []
    data_candidates = []
    top_level = []
    sampled_files = []
    scanned = 0
    truncated = False

    for item in sorted(root.iterdir(), key=lambda p: p.name):
        if item.name not in DEFAULT_EXCLUDES:
            top_level.append({"name": item.name, "type": "directory" if item.is_dir() else "file"})

    for current_text, dirs, files in os.walk(root):
        current = Path(current_text)
        current_depth = depth(root, current)
        dirs[:] = [d for d in sorted(dirs) if d not in DEFAULT_EXCLUDES and current_depth < max_depth]
        if current.name.lower() in DATA_NAMES:
            data_candidates.append(str(current.relative_to(root)))
        for name in sorted(files):
            if scanned >= max_files:
                truncated = True
                dirs[:] = []
                break
            path = current / name
            rel = str(path.relative_to(root))
            scanned += 1
            suffix = path.suffix.lower() or "<none>"
            extensions[suffix] += 1
            if len(sampled_files) < 200:
                sampled_files.append(rel)
            if name in BUILD_MARKERS:
                build_files.append({"path": rel, "hash": sha256(path)})
            if name in TEST_MARKERS or "test" in name.lower():
                if len(test_files) < 100:
                    test_files.append(rel)

    suggested = []
    if extensions.get(".java"):
        suggested.append({"analyzer_id": "java-spring", "reason": "java files observed", "state": "CANDIDATE"})
    if extensions.get(".sql") or data_candidates:
        suggested.append({"analyzer_id": "sql-database", "reason": "sql/data candidates observed", "state": "CANDIDATE"})
    if extensions.get(".yaml") or extensions.get(".yml") or extensions.get(".xml"):
        suggested.append({"analyzer_id": "interface-contract", "reason": "contract/config file candidates observed", "state": "CANDIDATE"})
        suggested.append({"analyzer_id": "batch-scheduler", "reason": "scheduler/workflow candidates may exist", "state": "CANDIDATE"})

    open_items = []
    if truncated:
        open_items.append({
            "open_id": "OPEN-INVENTORY-BUDGET",
            "type": "SEARCH_BUDGET_EXHAUSTED",
            "question": "Inventory budget 밖에 필요한 Source가 있는가?",
            "blocks_reasoning": False,
            "blocks_action": False,
            "escalation": "ENGINEERING_OWNER",
        })

    return {
        "schema_version": 1,
        "artifact_type": "SOURCE_INVENTORY",
        "source_inventory": {
            "source_root": str(root),
            "source_revision": source_revision,
            "truth": "OBSERVED",
            "scan": {
                "max_depth": max_depth,
                "max_files": max_files,
                "scanned_files": scanned,
                "truncated": truncated,
                "excludes": sorted(DEFAULT_EXCLUDES),
            },
            "top_level": top_level,
            "file_extensions": dict(sorted(extensions.items())),
            "build_markers": build_files,
            "test_candidates": test_files,
            "data_candidates": sorted(set(data_candidates)),
            "sampled_files": sampled_files,
            "suggested_analyzers": suggested,
            "open_items": open_items,
            "constraints": {
                "business_truth_confirmed": False,
                "program_relation_confirmed": False,
                "inventory_is_not_bounded_trace": True,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("source_revision")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = inventory(args.source_root, args.source_revision, args.max_depth, args.max_files)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
