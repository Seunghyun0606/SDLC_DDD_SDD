#!/usr/bin/env python3
"""Executable first-use setup for Greenfield/Brownfield projects.

Creates only runtime-consumed config, never infers Business Truth, and treats missing
technical facts as OPEN. Git presence alone is not Brownfield evidence.

User onboarding is intentionally routed to docs/00_시작/START_HERE.md. Setup must not
pretend that a first RQ exists when zero-to-one intake has not registered one yet.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = _load("setup_apply", SCRIPT_DIR / "apply_canonical_delta.py")
CONFIG = _load("setup_config", SCRIPT_DIR / "runtime_config.py")

USER_START_HERE = "docs/00_시작/START_HERE.md"
USER_SETUP_GUIDE = "docs/00_시작/프로젝트_설정_가이드.md"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:500_000]
    except OSError:
        return ""


def _project_python_exists(root: Path, roots: list[str]) -> bool:
    for rel in roots:
        base = root / rel
        if base.is_dir() and any(base.rglob("*.py")):
            return True
    return False


def _detect(root: Path) -> dict[str, Any]:
    pom = root / "pom.xml"
    gradle = next((p for p in [root / "build.gradle", root / "build.gradle.kts"] if p.is_file()), None)
    package = root / "package.json"
    pyproject = root / "pyproject.toml"
    source_roots = [x for x in ["src", "app", "apps", "packages", "lib", "server", "backend", "frontend"] if (root / x).exists()]
    test_roots = [x for x in ["tests", "test", "src/test"] if (root / x).exists()]
    resource_roots = [x for x in ["src/main/resources", "resources", "config"] if (root / x).exists()]
    language, framework, database = "OPEN", "OPEN", "OPEN"
    build_commands: list[str] = []
    test_commands: list[str] = []
    signals: list[str] = []
    gaps: list[str] = []

    if pom.is_file() or gradle:
        language = "Java"
        text = _read(pom) + ("\n" + _read(gradle) if gradle else "")
        if re.search(r"spring[-.]|org\.springframework|spring-boot", text, re.I):
            framework = "Spring"; signals.append("SPRING")
        if re.search(r"mybatis", text, re.I):
            signals.append("MYBATIS")
        if re.search(r"spring-data-jpa|hibernate|jakarta\.persistence|javax\.persistence", text, re.I):
            signals.append("JPA"); gaps.append("JPA 정밀 relation/runtime semantics는 정적 후보 이후 검토 필요")
        if re.search(r"kafka", text, re.I):
            signals.append("KAFKA"); gaps.append("Kafka runtime topology/schema는 Tool Evidence 필요")
        if pom.is_file():
            tool = "./mvnw" if (root / "mvnw").exists() else "mvn"
            build_commands, test_commands = [f"{tool} -q -DskipTests package"], [f"{tool} test"]
        else:
            tool = "./gradlew" if (root / "gradlew").exists() else "gradle"
            build_commands, test_commands = [f"{tool} assemble"], [f"{tool} test"]
    elif package.is_file():
        language = "JavaScript/TypeScript"
        text = _read(package)
        for marker, name in [(r'"react"\s*:', "React"), (r'"vue"\s*:', "Vue"), (r'"@angular/core"\s*:', "Angular"), (r'"next"\s*:', "Next.js")]:
            if re.search(marker, text): framework = name; break
        build_commands, test_commands = ["npm run build"], ["npm test -- --runInBand"]
        gaps.append("JavaScript/TypeScript Source relation Adapter는 현재 포함되지 않음")
    elif pyproject.is_file() or _project_python_exists(root, source_roots):
        language = "Python"
        if (root / "tests").exists(): test_commands = ["python -m pytest"]
        gaps.append("Python Source relation Adapter는 현재 포함되지 않음")

    schema_files = list(root.rglob("schema.sql"))[:20] + list(root.rglob("*.ddl"))[:20]
    if schema_files:
        database = "SQL_SCHEMA_PRESENT"; signals.append("DB_SCHEMA_FILE")

    brownfield = bool(source_roots or pom.is_file() or gradle or package.is_file() or pyproject.is_file() or schema_files)
    return {
        "detected_mode": "BROWNFIELD" if brownfield else "GREENFIELD",
        "language": language, "framework": framework, "database": database,
        "source_roots": source_roots, "test_roots": test_roots, "resource_roots": resource_roots,
        "build_commands": build_commands, "test_commands": test_commands,
        "signals": sorted(set(signals)), "coverage_gaps": gaps,
    }


def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _list(lines: list[str], indent: str, key: str, values: list[str]) -> None:
    if not values:
        lines.append(f"{indent}{key}: []")
    else:
        lines.append(f"{indent}{key}:")
        lines.extend(f"{indent}  - {_q(str(x))}" for x in values)


def _project_yaml(name: str, mode: str, delivery: str, customer: str, reverse: str, d: dict[str, Any]) -> str:
    return f'''project:
  name: {_q(name)}
  mode: {mode}
delivery:
  profile: {delivery}
  customer_documentation: {customer}
  reverse_analysis: {reverse}
bootstrap:
  generated_by: sdlc/scripts/bootstrap_project.py
  technology_status: {'DISCOVERED' if mode != 'GREENFIELD' else 'PROPOSE_OR_OPEN'}
technology:
  language: {_q(str(d['language']))}
  framework: {_q(str(d['framework']))}
  database: {_q(str(d['database']))}
documents:
  language: ko-KR
  human_metadata_mode: FRIENDLY
workflow:
  execution_guard_enabled: true
  protected_branches:
    - main
    - master
source_profile:
  path: sdlc/config/source-profile.yaml
agent_provider:
  path: sdlc/config/agent-provider.json
customization:
  overlay_order:
    - core
    - project_overlay
    - local_override
'''


def _source_yaml(d: dict[str, Any]) -> str:
    lines = ["schema_version: 1", "source:"]
    _list(lines, "  ", "roots", d["source_roots"])
    _list(lines, "  ", "test_roots", d["test_roots"])
    _list(lines, "  ", "resource_roots", d["resource_roots"])
    lines += [
        "  excludes:", "    - .git/**", "    - build/**", "    - target/**", "    - node_modules/**",
        "  existing_assets_first: true", "  static_analysis_first: true", "  full_repository_llm_scan: false", "build:",
    ]
    _list(lines, "  ", "commands", d["build_commands"])
    lines.append("test:"); _list(lines, "  ", "commands", d["test_commands"])
    lines += [
        "evidence:", "  hash_algorithm: sha256", "  preserve_file_path: true", "  preserve_symbol_locator: true",
        "  preserve_source_hash: true", "  observed_not_confirmed_business_truth: true",
        "write_policy:", "  min_target_confidence: MEDIUM", "  ambiguous_write: DEFERRED_TARGET_DECISION",
        "  dangerous_action_policy: EXECUTION_GUARD",
    ]
    return "\n".join(lines) + "\n"


def _provider(command_text: str | None) -> dict[str, Any]:
    command = shlex.split(command_text) if command_text else []
    return {
        "schema_version": 1, "provider_id": "PROJECT_AGENT_PROVIDER" if command else "UNCONFIGURED_PROVIDER",
        "provider_class": "EXTERNAL_AGENT" if command else "UNCONFIGURED", "enabled": bool(command),
        "timeout_seconds": 180, "result_filename": "stage-result.json", "command": command,
        "protected_branches": ["main", "master"], "allow_dirty_workspace": False,
        "allow_protected_branch_write": False, "allow_unverified_source_write": False,
    }


def bootstrap(root: Path, *, name: str, mode: str = "AUTO", delivery: str = "STANDARD", customer: str = "MINIMAL",
              reverse: str = "DIRECT_ONLY", provider_command: str | None = None, force: bool = False, validate: bool = True) -> dict[str, Any]:
    root = root.resolve(); d = _detect(root)
    resolved = d["detected_mode"] if mode.upper() == "AUTO" else mode.upper()
    if resolved not in {"GREENFIELD", "BROWNFIELD", "HYBRID"}: raise ValueError("mode must be AUTO/GREENFIELD/BROWNFIELD/HYBRID")
    delivery = delivery.upper()
    if delivery not in CONFIG.DELIVERY_PROFILES: raise ValueError("delivery must be FAST/STANDARD/FULL")
    paths = {
        "project": root / "sdlc/config/project-profile.yaml", "source": root / "sdlc/config/source-profile.yaml",
        "provider": root / "sdlc/config/agent-provider.json", "store": root / "sdlc/canonical/store.json",
    }
    writes: dict[str, str] = {}

    def write(path: Path, content: str) -> str:
        existed = path.exists(); path.parent.mkdir(parents=True, exist_ok=True)
        if existed and not force: return "EXISTING_KEPT"
        path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        return "UPDATED" if existed else "CREATED"

    writes["sdlc/config/project-profile.yaml"] = write(paths["project"], _project_yaml(name, resolved, delivery, customer.upper(), reverse.upper(), d))
    writes["sdlc/config/source-profile.yaml"] = write(paths["source"], _source_yaml(d))
    provider = _provider(provider_command)
    writes["sdlc/config/agent-provider.json"] = write(paths["provider"], json.dumps(provider, ensure_ascii=False, indent=2) + "\n")
    if not paths["store"].exists(): APPLY.save_store(paths["store"], APPLY.empty_store()); writes["sdlc/canonical/store.json"] = "CREATED"
    else: writes["sdlc/canonical/store.json"] = "EXISTING_KEPT"

    project_cfg, source_cfg = CONFIG.load_config(paths["project"]), CONFIG.load_config(paths["source"])
    if CONFIG.project_mode(project_cfg) != resolved: raise ValueError("generated project profile did not round-trip")
    expected_roots = sorted(set(d["source_roots"] + d["test_roots"] + d["resource_roots"]))
    if CONFIG.source_roots(source_cfg) != expected_roots: raise ValueError("generated source profile did not round-trip")

    validation = None
    validator = root / "sdlc/scripts/validate_harness_structure.py"
    if validate and validator.is_file():
        cp = subprocess.run([os.environ.get("PYTHON", "python"), str(validator), str(root)], cwd=root, text=True, capture_output=True, check=False)
        validation = {"exit_code": cp.returncode, "stdout": cp.stdout[-4000:], "stderr": cp.stderr[-4000:]}
    structure_ok = validation is None or validation["exit_code"] == 0
    provider_ready = bool(provider["enabled"] and provider["command"])
    adapter = "NONE"
    if resolved in {"BROWNFIELD", "HYBRID"}:
        if d["language"] == "Java" and "SPRING" in d["signals"]:
            adapter = "JAVA_SPRING_ENTERPRISE_STATIC_V0_2" if any(x in d["signals"] for x in ["JPA", "KAFKA"]) or "MYBATIS" not in d["signals"] else "JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1"
        else: adapter = "PROJECT_ADAPTER_REQUIRED_OR_CORE_PARTIAL"
    opens = [label for label, value in [("개발 언어", d["language"]), ("Framework", d["framework"]), ("DB", d["database"])] if value == "OPEN"]
    if not provider_ready: opens.append("실제 Agent Provider command")
    if resolved in {"BROWNFIELD", "HYBRID"} and not d["source_roots"]: opens.append("실제 Source root")
    status = "READY_FOR_PLAN" if provider_ready and structure_ok else "HARNESS_VALIDATION_FAILED" if not structure_ok else "CONFIGURED_PROVIDER_REQUIRED"
    report = {
        "schema_version": 1, "status": status, "project_name": name, "mode": resolved, "delivery_profile": delivery,
        "detected": d, "adapter_assessment": adapter, "provider_ready": provider_ready, "open_items": opens, "writes": writes,
        "validation": validation,
        "user_entrypoint": {
            "start_here": USER_START_HERE,
            "project_setup_guide": USER_SETUP_GUIDE,
            "message": "일반 사용자는 Framework 내부 Config/Contract보다 START_HERE에서 다음 행동을 확인한다.",
            "zero_to_one_intake": "WP03_NOT_YET_CONNECTED",
        },
        "next_commands": ["python sdlc/scripts/harness.py check --setup"],
        "next_if_target_exists": [
            "python sdlc/scripts/harness.py check --target <RQ-ID>",
            "python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only",
        ],
        "next_if_no_target": "START_HERE의 요구사항 등록 안내를 따른다. 현재 신규 RQ 자동 등록은 WP-03 미구현이므로 내부 Canonical을 수동 편집하지 않는다.",
    }
    result_path = root / "sdlc/runtime/setup/setup-result.json"; result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bootstrap minimum executable SDLC Harness project configuration.")
    ap.add_argument("--root", default="."); ap.add_argument("--name", default="project"); ap.add_argument("--mode", default="AUTO")
    ap.add_argument("--delivery", default="STANDARD"); ap.add_argument("--customer", default="MINIMAL"); ap.add_argument("--reverse", default="DIRECT_ONLY")
    ap.add_argument("--provider-command"); ap.add_argument("--force", action="store_true"); ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = bootstrap(Path(args.root), name=args.name, mode=args.mode, delivery=args.delivery, customer=args.customer,
                           reverse=args.reverse, provider_command=args.provider_command, force=args.force, validate=not args.no_validate)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "SETUP_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "READY_FOR_PLAN" else 4


if __name__ == "__main__": raise SystemExit(main())
