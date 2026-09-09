#!/usr/bin/env python3
"""Validate committed human-facing templates against the plain-language contract.

This validator deliberately does not scan machine contracts, runtime JSON, Agent internal references,
or fenced code examples. It checks the visible Markdown body of active human-facing templates so raw
machine states do not leak back into generated review documents.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


CONTRACT_PATH = "sdlc/design/contracts/human-facing-language-contract.json"
DEFAULT_ROOTS = [
    "sdlc/templates/engineering",
    "sdlc/templates/customer",
    "sdlc/custom/project/templates",
]


def _visible_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^---\s*$.*?^---\s*$", "", text, count=1, flags=re.S | re.M)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return text


def _load_contract(root: Path) -> dict[str, Any]:
    path = root / CONTRACT_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"contract object required: {path}")
    return data


def _markdown_files(root: Path, roots: list[str]) -> list[Path]:
    result: list[Path] = []
    for rel in roots:
        base = root / rel
        if not base.exists():
            continue
        if base.is_file() and base.suffix.lower() == ".md":
            result.append(base)
        elif base.is_dir():
            result.extend(path for path in base.rglob("*.md") if path.is_file())
    return sorted(set(result))


def validate(root: Path, *, roots: list[str] | None = None) -> list[dict[str, Any]]:
    root = root.resolve()
    contract = _load_contract(root)
    forbidden = [str(x) for x in contract.get("human_visible_forbidden_raw_terms", []) if str(x)]
    errors: list[dict[str, Any]] = []
    for path in _markdown_files(root, roots or DEFAULT_ROOTS):
        visible = _visible_markdown(path.read_text(encoding="utf-8"))
        for term in forbidden:
            if term not in visible:
                continue
            lines = [index for index, line in enumerate(visible.splitlines(), start=1) if term in line]
            errors.append({
                "code": "RAW_MACHINE_OR_UNFRIENDLY_TERM_VISIBLE",
                "path": path.relative_to(root).as_posix(),
                "term": term,
                "visible_line_candidates": lines[:10],
                "preferred": contract.get("preferred_terms", {}).get(term),
            })
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate human-facing Markdown terminology.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--scan-root", action="append", default=[])
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        errors = validate(root, roots=args.scan_root or None)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    result = {
        "status": "PASS" if not errors else "FAIL",
        "contract": CONTRACT_PATH,
        "errors": errors,
        "checked_roots": args.scan_root or DEFAULT_ROOTS,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
