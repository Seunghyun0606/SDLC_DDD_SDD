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
Agent execution is vendor-neutral: INTERACTIVE is the default; HEADLESS is opt-in.
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


def _drop_option(args: list[str], option: str) -> list[str]:
    """Drop ``--option value`` and ``--option=value`` from routed argv."""
    out: list[str] = []
    skip = False
    for value in args:
        if skip:
            skip = False
            continue
        if value == option:
            skip = True
            continue
        if value.startswith(option + "="):
            continue
        out.append(value)
    return out


def _runtime_profile_args(args: list[str]) -> tuple[list[str], dict]:
    """Resolve project entry and append machine-only effective artifacts plus Agent runtime."""
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
    execution = json.loads(paths["agent_execution"].read_text(encoding="utf-8"))
    resolved["agent_runtime"] = execution

    routed = list(args)
    routed = _drop_option(routed, "--project-profile")
    routed = _drop_option(routed, "--source-profile")
    routed = _drop_option(routed, "--provider-config")
    routed += ["--project-profile", str(paths["project_profile"]), "--source-profile", str(paths["source_profile"])]
    if execution.get("execution_mode") == "HEADLESS":
        routed += ["--provider-config", str(paths["provider_config"])]
    return routed, resolved


def _connect_provider_from_setup_args(setup, args: list[str], result: dict) -> dict:
    """Backward-compatible ``--provider-command`` bridge for existing automation users.

    New projects should configure HEADLESS under ``.sdlc/project.yaml``. This bridge deliberately
    keeps the old provider JSON only as a legacy fallback and marks it deprecated.
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
    effective = config.materialize_effective_profiles(root, resolved, provider_config_path=provider_path)
    execution = json.loads(effective["agent_execution"].read_text(encoding="utf-8"))

    result["agent_execution"] = execution
    result["provider_ready"] = execution.get("execution_mode") == "HEADLESS" and bool(execution.get("ready"))
    result["status"] = "READY_FOR_PLAN"
    result["open_items"] = [x for x in result.get("open_items", []) if x != "실제 Agent Provider command"]
    result.setdefault("writes", {})[config.DEFAULT_PROVIDER_CONFIG_PATH] = "UPDATED_BY_LEGACY_SETUP_OPTION"
    result["provider_connection"] = {
        "status": "CONNECTED_LEGACY_COMPATIBILITY",
        "deprecated": True,
        "project_config_preserved": True,
        "message": "--provider-command는 호환 경로입니다. 신규 자동화는 .sdlc/project.yaml의 agent.execution=HEADLESS를 사용하세요.",
    }
    return result


def _run_setup(args: list[str]) -> int:
    """Bootstrap project config. INTERACTIVE is ready without any Provider setup."""
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
        root = _root_from_args(args)
        config = _load("harness_setup_mode_config", "runtime_config.py")
        try:
            resolved = config.resolve_runtime_config(root)
            provider_path = root / config.DEFAULT_PROVIDER_CONFIG_PATH
            legacy = config.load_config(provider_path) if provider_path.is_file() else {}
            execution = config.resolve_agent_runtime(resolved["project"], legacy_provider=legacy)
            result["agent_execution"] = {key: value for key, value in execution.items() if key != "provider_config"}
            if execution["execution_mode"] == "INTERACTIVE":
                result["status"] = "READY_FOR_PLAN"
                result["provider_ready"] = False
                result["open_items"] = [x for x in result.get("open_items", []) if x != "실제 Agent Provider command"]
                result["message"] = "현재 IDE/CLI Agent를 사용하는 INTERACTIVE 실행 준비가 완료되었습니다. 별도 Provider 설정은 필요하지 않습니다."
                code = 0
            elif execution.get("ready"):
                result["status"] = "READY_FOR_PLAN"
                code = 0
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            result["status"] = "SETUP_FAILED"
            result["error"] = str(exc)
            code = 2

        result["user_entrypoint"] = {
            "start_here": "docs/00_시작/START_HERE.md",
            "project_setup_guide": "docs/00_시작/프로젝트_설정_가이드.md",
            "zero_to_one_intake": "CONNECTED",
            "message": "setup 확인 후 요구사항 원본을 intake하고 현재 Agent에서 work를 진행한다.",
        }
        result["next_commands"] = [
            "python sdlc/scripts/harness.py check --setup",
            "python sdlc/scripts/harness.py intake <requirement-file.xlsx>",
        ]
        result.pop("next_if_target_exists", None)
        result.pop("next_if_no_target", None)
        result_path = root / "sdlc/runtime/setup/setup-result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    print(raw)
    return code


def _run_check(args: list[str]) -> int:
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
            args, resolved = _runtime_profile_args(args)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(json.dumps({"status": "PROJECT_CONFIG_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
        mode = str((resolved.get("agent_runtime") or {}).get("execution_mode") or "INTERACTIVE")
        if command == "work":
            if mode == "INTERACTIVE":
                return _load("harness_interactive_work", "interactive_work.py").main(_drop_option(args, "--provider-config"))
            return _load("harness_work_handoff", "work_handoff.py").main(args)
        if mode == "INTERACTIVE":
            return _load("harness_interactive_change", "interactive_change.py").main(_drop_option(args, "--provider-config"))
        return _load("harness_change", "run_change.py").main(args)
    if command == "check":
        return _run_check(args)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
