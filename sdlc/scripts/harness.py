#!/usr/bin/env python3
"""Single executable entry point for non-expert project users.

Examples:
  python sdlc/scripts/harness.py setup --name my-project --mode AUTO
  python sdlc/scripts/harness.py check --setup
  python sdlc/scripts/harness.py work --target RQ-001 --plan-only
  python sdlc/scripts/harness.py change --target RQ-001 --change "환불 상태 조회 추가"
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help", "help"}:
        print(__doc__.strip())
        print("\nCommands: setup | work | change | check")
        return 0
    command = args.pop(0).lower()
    if command == "setup":
        return _load("harness_setup", "bootstrap_project.py").main(args)
    if command == "work":
        return _load("harness_work", "run_work.py").main(args)
    if command == "change":
        return _load("harness_change", "run_change.py").main(args)
    if command == "check":
        return _load("harness_check", "run_check.py").main(args)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
