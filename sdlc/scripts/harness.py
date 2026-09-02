#!/usr/bin/env python3
"""Single executable entry point for non-expert project users.

Examples:
  python sdlc/scripts/harness.py setup --name my-project --mode AUTO
  python sdlc/scripts/harness.py check --setup
  python sdlc/scripts/harness.py work --target RQ-001 --plan-only
  python sdlc/scripts/harness.py change --target RQ-001 --change "환불 상태 조회 추가"

Project users maintain one setting file: .sdlc/project.yaml.
"""
from __future__ import annotations

import importlib.util
import json
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


def _root_from_args(args: list[str]) -> Path:
    for i, value in enumerate(args):
        if value == "--root" and i + 1 < len(args):
            return Path(args[i + 1]).resolve()
        if value.startswith("--root="):
            return Path(value.split("=", 1)[1]).resolve()
    return Path(".").resolve()


def _value_from_args(args: list[str], option: str, default: str) -> str:
    for i, value in enumerate(args):
        if value == option and i + 1 < len(args):
            return args[i + 1]
        if value.startswith(option + "="):
            return value.split("=", 1)[1]
    return default


def _runtime_profile_args(args: list[str]) -> tuple[list[str], dict]:
    """Resolve the single project entry and append machine-only effective artifacts.

    Effective paths are appended last so ``.sdlc/project.yaml`` remains authoritative even
    when stale legacy profile/provider arguments were supplied by an old wrapper.
    """
    config = _load("harness_runtime_config", "runtime_config.py")
    root = _root_from_args(args)
    resolved = config.resolve_runtime_config(root)
    if resolved["source_kind"] == "UNCONFIGURED":
        raise ValueError(f"project configuration missing: {config.PROJECT_ENTRY_PATH}; run harness.py setup first")
    provider_raw = _value_from_args(args, "--provider-config", config.DEFAULT_PROVIDER_CONFIG_PATH)
    provider_path = Path(provider_raw)
    if not provider_path.is_absolute():
        provider_path = root / provider_path
    paths = config.materialize_effective_profiles(root, resolved, provider_config_path=provider_path)
    routed = list(args)
    routed += ["--project-profile", str(paths["project_profile"]), "--source-profile", str(paths["source_profile"])]
    if "provider_config" in paths:
        routed += ["--provider-config", str(paths["provider_config"])]
    return routed, resolved


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help", "help"}:
        print(__doc__.strip())
        print("\nCommands: setup | work | change | check")
        return 0
    command = args.pop(0).lower()
    if command == "setup":
        return _load("harness_setup", "bootstrap_project.py").main(args)
    if command in {"work", "change"}:
        try:
            args, _ = _runtime_profile_args(args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "PROJECT_CONFIG_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
        if command == "work":
            return _load("harness_work", "run_work.py").main(args)
        return _load("harness_change", "run_change.py").main(args)
    if command == "check":
        return _load("harness_check", "run_check.py").main(args)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
