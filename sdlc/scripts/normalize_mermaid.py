#!/usr/bin/env python3
"""Normalize Mermaid flowchart labels for GitHub Markdown rendering.

GitHub's Mermaid parser can interpret labels such as ``S[/setup]`` as shape
syntax and fail lexically when the shape is incomplete. This tool rewrites
plain flowchart node labels to quoted Mermaid labels while preserving explicit
shape syntaxes such as ``A[/text/]`` and ``A[(database)]``.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"(^```mermaid\s*\n)(.*?)(^```\s*$)", re.MULTILINE | re.DOTALL)
RECT_RE = re.compile(r"(?<![\w-])([A-Za-z_][A-Za-z0-9_-]*)\[(?!\")([^\]\n]+)\]")
DIAMOND_RE = re.compile(r"(?<![\w-])([A-Za-z_][A-Za-z0-9_-]*)\{(?!\")([^}\n]+)\}")


def _escape_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', "&quot;")


def _is_explicit_rect_shape(label: str) -> bool:
    stripped = label.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        return True  # cylinder/database: A[(text)]
    if len(stripped) >= 2 and stripped[0] in "/\\" and stripped[-1] in "/\\":
        return True  # parallelogram/trapezoid family
    return False


def normalize_block(block: str) -> str:
    first = next((line.strip() for line in block.splitlines() if line.strip()), "")
    if not (first.startswith("flowchart ") or first.startswith("graph ")):
        return block

    def rect_sub(match: re.Match[str]) -> str:
        node_id, label = match.group(1), match.group(2)
        if _is_explicit_rect_shape(label):
            return match.group(0)
        return f'{node_id}["{_escape_label(label.strip())}"]'

    def diamond_sub(match: re.Match[str]) -> str:
        node_id, label = match.group(1), match.group(2)
        return f'{node_id}{{"{_escape_label(label.strip())}"}}'

    block = RECT_RE.sub(rect_sub, block)
    block = DIAMOND_RE.sub(diamond_sub, block)
    return block


def normalize_text(text: str) -> str:
    def fence_sub(match: re.Match[str]) -> str:
        return match.group(1) + normalize_block(match.group(2)) + match.group(3)
    return FENCE_RE.sub(fence_sub, text)


def iter_markdown(paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".md":
            found.add(path)
        elif path.is_dir():
            found.update(p for p in path.rglob("*.md") if ".git" not in p.parts)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=["."], help="Markdown file(s) or directories")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Rewrite files in place")
    mode.add_argument("--check", action="store_true", help="Fail if normalization is needed")
    args = parser.parse_args()

    files = iter_markdown([Path(p) for p in args.paths])
    changed: list[Path] = []
    for path in files:
        original = path.read_text(encoding="utf-8")
        normalized = normalize_text(original)
        if normalized != original:
            changed.append(path)
            if args.write:
                path.write_text(normalized, encoding="utf-8")

    if args.write:
        for path in changed:
            print(f"normalized: {path}")
        return 0

    if changed:
        for path in changed:
            print(f"Mermaid label normalization required: {path}", file=sys.stderr)
        print("Run: python sdlc/scripts/normalize_mermaid.py --write .", file=sys.stderr)
        return 1

    print(f"Mermaid labels OK ({len(files)} Markdown files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
