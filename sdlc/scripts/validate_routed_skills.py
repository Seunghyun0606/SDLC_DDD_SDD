#!/usr/bin/env python3
"""Validate only skills that are reachable from the active stage-routing contract."""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import yaml

REQUIRED_SECTIONS = [
    "Purpose",
    "Required Input",
    "Optional Input",
    "Precondition",
    "Retrieval Strategy",
    "Atomic Steps",
    "Decision Rules",
    "Output Schema",
    "Quality Check",
    "Alert Conditions",
    "Stop Conditions",
    "Escalation Conditions",
    "Do Not",
    "Example",
]


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def routed_skill_names(routing):
    names = set()
    for rule in (routing.get("stages") or {}).values():
        if rule.get("skill"):
            names.add(rule["skill"])
    for command, rule in (routing.get("commands") or {}).items():
        if command != "/work" and rule.get("skill"):
            names.add(rule["skill"])
    return sorted(names)


def headings(text):
    found = []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            found.append(match.group(1).strip())
    return found


def validate_skill(path: Path):
    if not path.is_file():
        return [f"LSK-001: routed skill missing: {path}"]
    text = path.read_text(encoding="utf-8")
    current = headings(text)
    errors = []
    for section in REQUIRED_SECTIONS:
        if section not in current:
            errors.append(f"LSK-002: {path}: missing section '{section}'")
    positions = [current.index(section) for section in REQUIRED_SECTIONS if section in current]
    if len(positions) == len(REQUIRED_SECTIONS) and positions != sorted(positions):
        errors.append(f"LSK-003: {path}: required sections are out of contract order")
    if "OPEN" not in text:
        errors.append(f"LSK-004: {path}: OPEN handling must be explicit")
    if "Evidence" not in text and "evidence" not in text:
        errors.append(f"LSK-005: {path}: Evidence handling must be explicit")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("routing", type=Path)
    parser.add_argument("skills_root", type=Path)
    args = parser.parse_args()
    routing = load(args.routing)
    errors = []
    for name in routed_skill_names(routing):
        errors.extend(validate_skill(args.skills_root / name / "SKILL.md"))
    if errors:
        print("\n".join(errors))
        return 1
    print("OK: all routed skills satisfy low-agent section contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
