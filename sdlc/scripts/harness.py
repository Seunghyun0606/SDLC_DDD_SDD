#!/usr/bin/env python3
"""Single executable entry point for non-expert project users.

Examples:
  python sdlc/scripts/harness.py setup --name my-project --mode AUTO
  python sdlc/scripts/harness.py intake requirements.xlsx
  python sdlc/scripts/harness.py check --setup
  python sdlc/scripts/harness.py work --target RQ-001
  python sdlc/scripts/harness.py review --target RQ-001 --by 홍길동 --answer "승인 주체는 팀장"
  python sdlc/scripts/harness.py change --target RQ-001 --change "환불 상태 조회 추가"

Project users maintain one setting file: .sdlc/project.yaml.
They do not need to edit Rule/Skill/Reference/Contract files or blank stage templates.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
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


def _has_flag(args: list[str], option: str) -> bool:
    return option in args


def _runtime_profile_args(args: list[str]) -> tuple[list[str], dict]:
    """Resolve the single project entry and append machine-only effective artifacts."""
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


def _connect_provider_from_setup_args(setup, args: list[str], result: dict) -> dict:
    """Allow official setup to connect a Provider later without rewriting project.yaml.

    ``bootstrap_project.py`` intentionally preserves existing user files unless ``--force`` is
    supplied. For first-use UX that meant a Provider command supplied on a later setup run could
    not replace the initial UNCONFIGURED provider without either editing an internal JSON file or
    forcing the whole project entry. The official harness fixes only that handoff: project.yaml is
    still preserved, while an explicitly supplied Provider command updates the machine Provider
    config and regenerates effective runtime profiles.
    """
    provider_command = _value_from_args(args, "--provider-command", "").strip()
    if not provider_command:
        return result

    root = _root_from_args(args)
    config = _load("harness_setup_runtime_config", "runtime_config.py")
    resolved = config.resolve_runtime_config(root)
    if resolved["source_kind"] == "UNCONFIGURED":
        return result

    protected = config.nested(resolved["project"], "git", "protected_branches", default=["main", "master"])
    provider = setup._provider(provider_command, list(protected or ["main", "master"]))
    provider_path = root / config.DEFAULT_PROVIDER_CONFIG_PATH
    provider_path.parent.mkdir(parents=True, exist_ok=True)
    provider_path.write_text(json.dumps(provider, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    config.materialize_effective_profiles(root, resolved, provider_config_path=provider_path)

    result["provider_ready"] = True
    result["status"] = "READY_FOR_PLAN"
    result["open_items"] = [x for x in result.get("open_items", []) if x != "실제 Agent Provider command"]
    result.setdefault("writes", {})[config.DEFAULT_PROVIDER_CONFIG_PATH] = "UPDATED_BY_OFFICIAL_SETUP"
    result["provider_connection"] = {
        "status": "CONNECTED",
        "project_config_preserved": True,
        "message": "Provider command만 갱신했으며 .sdlc/project.yaml은 다시 작성하지 않았습니다.",
    }
    return result


def _run_setup(args: list[str]) -> int:
    """Keep bootstrap safety semantics but expose a non-blocking first-use handoff."""
    setup = _load("harness_setup", "bootstrap_project.py")
    captured = StringIO()
    with redirect_stdout(captured):
        code = setup.main(args)
    raw = captured.getvalue().strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return code
    if isinstance(result, dict) and result.get("status") != "SETUP_FAILED":
        result = _connect_provider_from_setup_args(setup, args, result)
        if result.get("status") == "CONFIGURED_PROVIDER_REQUIRED":
            result["status"] = "SETUP_READY_PROVIDER_PENDING"
            result["work_blocked_reason"] = "Agent Provider가 아직 연결되지 않았습니다. setup/intake는 계속 진행할 수 있고 work에서만 Provider가 필요합니다."
            code = 0
        elif result.get("status") == "READY_FOR_PLAN":
            code = 0

        result["user_entrypoint"] = {
            "start_here": "docs/00_시작/START_HERE.md",
            "project_setup_guide": "docs/00_시작/프로젝트_설정_가이드.md",
            "zero_to_one_intake": "CONNECTED",
            "message": "setup 확인 후 요구사항 원본을 intake하면 실제 RQ Target과 다음 work 명령을 받는다.",
        }
        result["next_commands"] = [
            "python sdlc/scripts/harness.py check --setup",
            "python sdlc/scripts/harness.py intake <requirement-file.xlsx>",
        ]
        result.pop("next_if_target_exists", None)
        result.pop("next_if_no_target", None)
        root = _root_from_args(args)
        result_path = root / "sdlc/runtime/setup/setup-result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    print(raw)
    return code


def _run_check(args: list[str]) -> int:
    """Show setup readiness without treating a not-yet-connected Provider as setup failure."""
    check = _load("harness_check", "run_check.py")
    captured = StringIO()
    with redirect_stdout(captured):
        code = check.main(args)
    raw = captured.getvalue().strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return code

    if _has_flag(args, "--setup") and result.get("status") == "SETUP_OR_PROVIDER_REQUIRED":
        setup = result.get("setup") or {}
        provider = setup.get("provider") or {}
        config_ready = bool(setup.get("project_config") and setup.get("canonical_store"))
        if config_ready and not provider.get("enabled"):
            result["status"] = "SETUP_READY_PROVIDER_PENDING"
            result["message"] = "프로젝트 설정은 사용할 수 있습니다. 요구사항 intake는 진행할 수 있으며 Agent work 전에만 Provider 연결이 필요합니다."
            result["work_blocked_reason"] = "AGENT_PROVIDER_PENDING"
            code = 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help", "help"}:
        print(__doc__.strip())
        print("\nCommands: setup | intake | work | review | change | check")
        return 0
    command = args.pop(0).lower()
    if command == "setup":
        return _run_setup(args)
    if command == "intake":
        return _load("harness_intake", "intake_requirements.py").main(args)
    if command == "review":
        return _load("harness_review", "review_work.py").main(args)
    if command in {"work", "change"}:
        try:
            args, _ = _runtime_profile_args(args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "PROJECT_CONFIG_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
        if command == "work":
            return _load("harness_work_handoff", "work_handoff.py").main(args)
        return _load("harness_change", "run_change.py").main(args)
    if command == "check":
        return _run_check(args)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
