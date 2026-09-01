#!/usr/bin/env python3
"""Executable /setup bootstrap for first-time Greenfield/Brownfield adoption.

The bootstrap creates only runtime-consumed project files. It discovers technical facts
conservatively, never treats Git existence alone as Brownfield Source evidence, never
invents business facts, and keeps missing information OPEN.
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


def _text(path: Path, limit: int = 500_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _detect(root: Path) -> dict[str, Any]:
    pom = root / "pom.xml"
    gradles = [root / "build.gradle", root / "build.gradle.kts"]
    package = root / "package.json"
    pyproject = root / "pyproject.toml"
    source_candidates = ["src", "app", "apps", "packages", "lib", "server", "backend", "frontend"]
    source_roots = [name for name in source_candidates if (root / name).exists()]
    test_candidates = ["tests", "test", "src/test"]
    test_roots = [name for name in test_candidates if (root / name).exists()]
    resource_candidates = ["src/main/resources", "resources", "config"]
    resource_roots = [name for name in resource_candidates if (root / name).exists()]

    language = "OPEN"
    framework = "OPEN"
    database = "OPEN"
    build_commands: list[str] = []
    test_commands: list[str] = []
    signals: list[str] = []
    unsupported: list[str] = []

    if pom.is_file() or any(p.is_file() for p in gradles):
        language = "Java"
        build_text = _text(pom) + "\n" + "\n".join(_text(p) for p in gradles if p.is_file())
        if re.search(r"spring[-.]|org\.springframework|spring-boot", build_text, re.I):
            framework = "Spring"
            signals.append("SPRING")
        if re.search(r"mybatis", build_text, re.I):
            signals.append("MYBATIS")
        if re.search(r"spring-data-jpa|hibernate|jakarta\.persistence|javax\.persistence", build_text, re.I):
            signals.append("JPA")
            unsupported.append("JPA 정밀 relation은 Extended Java Adapter도 정적 후보 수준이므로 Coverage Gap 검토 필요")
        if re.search(r"kafka", build_text, re.I):
            signals.append("KAFKA")
            unsupported.append("Kafka runtime topology/schema는 Source 정적 분석만으로 확정할 수 없어 Tool Evidence가 필요")
        if pom.is_file():
            if (root / "mvnw").exists():
                build_commands, test_commands = ["./mvnw -q -DskipTests package"], ["./mvnw test"]
            else:
                build_commands, test_commands = ["mvn -q -DskipTests package"], ["mvn test"]
        else:
            if (root / "gradlew").exists():
                build_commands, test_commands = ["./gradlew assemble"], ["./gradlew test"]
            else:
                build_commands, test_commands = ["gradle assemble"], ["gradle test"]
    elif package.is_file():
        language = "JavaScript/TypeScript"
        data = _text(package)
        if re.search(r'"react"\s*:', data):
            framework = "React"
        elif re.search(r'"vue"\s*:', data):
            framework = "Vue"
        elif re.search(r'"@angular/core"\s*:', data):
            framework = "Angular"
        elif re.search(r'"next"\s*:', data):
            framework = "Next.js"
        build_commands, test_commands = ["npm run build"], ["npm test -- --runInBand"]
        unsupported.append("JavaScript/TypeScript Source relation 분석 Adapter는 현재 배포에 포함되지 않음")
    elif pyproject.is_file() or any(root.rglob("*.py")):
        language = "Python"
        test_commands = ["python -m pytest"] if (root / "tests").exists() else []
        unsupported.append("Python Source relation 분석 Adapter는 현재 배포에 포함되지 않음")

    schema_files = list(root.rglob("schema.sql"))[:20] + list(root.rglob("*.ddl"))[:20]
    if schema_files:
        database = "SQL_SCHEMA_PRESENT"
        signals.append("DB_SCHEMA_FILE")

    brownfield_signals = bool(source_roots or pom.is_file() or package.is_file() or pyproject.is_file() or schema_files)
    return {
        "detected_mode": "BROWNFIELD" if brownfield_signals else "GREENFIELD",
        "language": language,
        "framework": framework,
        "database": database,
        "source_roots": source_roots,
        "test_roots": test_roots,
        "resource_roots": resource_roots,
        "build_commands": build_commands,
        "test_commands": test_commands,
        "signals": sorted(set(signals)),
        "coverage_gaps": unsupported,
    }


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _yaml_list(lines: list[str], indent: str, key: str, values: list[str]) -> None:
    if not values:
        lines.append(f"{indent}{key}: []")
        return
    lines.append(f"{indent}{key}:")
    lines.extend(f"{indent}  - {_yaml_quote(str(value))}" for value in values)


def _project_yaml(name: str, mode: str, delivery: str, customer: str, reverse: str, detected: dict[str, Any]) -> str:
    return f"""project:
  name: {_yaml_quote(name)}
  mode: {mode}
delivery:
  profile: {delivery}  # FAST | STANDARD | FULL
  customer_documentation: {customer}  # NONE | MINIMAL | STANDARD
  reverse_analysis: {reverse}  # OFF | DIRECT_ONLY | RELATED_GRAPH
bootstrap:
  generated_by: sdlc/scripts/bootstrap_project.py
  technology_status: {'DISCOVERED' if mode != 'GREENFIELD' else 'PROPOSE_OR_OPEN'}
technology:
  language: {_yaml_quote(str(detected['language']))}
  framework: {_yaml_quote(str(detected['framework']))}
  database: {_yaml_quote(str(detected['database']))}
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
"""


def _source_yaml(detected: dict[str, Any], mode: str) -> str:
    lines = ["schema_version: 1", "source:"]
    _yaml_list(lines, "  ", "roots", list(detected["source_roots"]))
    _yaml_list(lines, "  ", "test_roots", list(detected["test_roots"]))
    _yaml_list(lines, "  ", "resource_roots", list(detected.get("resource_roots", [])))
    lines += [
        "  excludes:", "    - .git/**", "    - build/**", "    - target/**", "    - node_modules/**",
        "  existing_assets_first: true", "  static_analysis_first: true", "  full_repository_llm_scan: false",
        "build:",
    ]
    _yaml_list(lines, "  ", "commands", list(detected["build_commands"]))
    lines.append("test:")
    _yaml_list(lines, "  ", "commands", list(detected["test_commands"]))
    lines += [
        "evidence:", "  hash_algorithm: sha256", "  preserve_file_path: true", "  preserve_symbol_locator: true",
        "  preserve_source_hash: true", "  observed_not_confirmed_business_truth: true",
        "write_policy:", "  min_target_confidence: MEDIUM", "  ambiguous_write: DEFERRED_TARGET_DECISION",
        "  dangerous_action_policy: EXECUTION_GUARD",
    ]
    return "\n".join(lines) + "\n"


def _provider_json(command_text: str | None) -> dict[str, Any]:
    command = shlex.split(command_text) if command_text else []
    return {
        "schema_version": 1,
        "provider_id": "PROJECT_AGENT_PROVIDER" if command else "UNCONFIGURED_PROVIDER",
        "provider_class": "EXTERNAL_AGENT" if command else "UNCONFIGURED",
        "enabled": bool(command),
        "timeout_seconds": 180,
        "result_filename": "stage-result.json",
        "command": command,
        "protected_branches": ["main", "master"],
        "allow_dirty_workspace": False,
        "allow_protected_branch_write": False,
        "allow_unverified_source_write": False,
    }


def bootstrap(
    root: Path, *, name: str, mode: str = "AUTO", delivery: str = "STANDARD",
    customer: str = "MINIMAL", reverse: str = "DIRECT_ONLY", provider_command: str | None = None,
    force: bool = False, validate: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    detected = _detect(root)
    resolved_mode = detected["detected_mode"] if mode.upper() == "AUTO" else mode.upper()
    if resolved_mode not in {"GREENFIELD", "BROWNFIELD", "HYBRID"}:
        raise ValueError("mode must be AUTO/GREENFIELD/BROWNFIELD/HYBRID")
    delivery = delivery.upper()
    if delivery not in CONFIG.DELIVERY_PROFILES:
        raise ValueError("delivery must be FAST/STANDARD/FULL")
    customer = customer.upper()
    reverse = reverse.upper()

    project_path = root / "sdlc/config/project-profile.yaml"
    source_path = root / "sdlc/config/source-profile.yaml"
    provider_path = root / "sdlc/config/agent-provider.json"
    store_path = root / "sdlc/canonical/store.json"
    writes: dict[str, str] = {}

    def write_text(path: Path, content: str) -> str:
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        if existed and not force:
            return "EXISTING_KEPT"
        path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        return "UPDATED" if existed else "CREATED"

    writes[str(project_path.relative_to(root))] = write_text(project_path, _project_yaml(name, resolved_mode, delivery, customer, reverse, detected))
    writes[str(source_path.relative_to(root))] = write_text(source_path, _source_yaml(detected, resolved_mode))
    provider = _provider_json(provider_command)
    writes[str(provider_path.relative_to(root))] = write_text(provider_path, json.dumps(provider, ensure_ascii=False, indent=2) + "\n")
    if not store_path.exists():
        APPLY.save_store(store_path, APPLY.empty_store())
        writes[str(store_path.relative_to(root))] = "CREATED"
    else:
        writes[str(store_path.relative_to(root))] = "EXISTING_KEPT"

    parsed_project = CONFIG.load_config(project_path)
    parsed_source = CONFIG.load_config(source_path)
    if CONFIG.project_mode(parsed_project) != resolved_mode:
        raise ValueError("generated project-profile mode did not round-trip")
    expected_roots = sorted(set([*detected["source_roots"], *detected["test_roots"], *detected.get("resource_roots", [])]))
    if CONFIG.source_roots(parsed_source) != expected_roots:
        raise ValueError("generated source-profile roots did not round-trip")

    validation = None
    validator = root / "sdlc/scripts/validate_harness_structure.py"
    if validate and validator.is_file():
        cp = subprocess.run([os.environ.get("PYTHON", "python"), str(validator), str(root)], cwd=str(root), text=True, capture_output=True, check=False)
        validation = {"exit_code": cp.returncode, "stdout": cp.stdout[-4000:], "stderr": cp.stderr[-4000:]}

    provider_ready = bool(provider["enabled"] and provider["command"])
    adapter = "NONE"
    if resolved_mode in {"BROWNFIELD", "HYBRID"}:
        if detected["language"] == "Java" and "SPRING" in detected["signals"]:
            adapter = "JAVA_SPRING_ENTERPRISE_STATIC_V0_2" if any(x in detected["signals"] for x in ["JPA", "KAFKA"]) else "JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1" if "MYBATIS" in detected["signals"] else "JAVA_SPRING_ENTERPRISE_STATIC_V0_2"
        else:
            adapter = "PROJECT_ADAPTER_REQUIRED_OR_CORE_PARTIAL"
    open_items = []
    for label, value in [("개발 언어", detected["language"]), ("Framework", detected["framework"]), ("DB", detected["database"])]:
        if value == "OPEN":
            open_items.append(label)
    if not provider_ready:
        open_items.append("실제 Agent Provider command")
    if resolved_mode in {"BROWNFIELD", "HYBRID"} and not detected["source_roots"]:
        open_items.append("실제 Source root")

    structure_ok = validation is None or validation["exit_code"] == 0
    status = "READY_FOR_PLAN" if provider_ready and structure_ok else "HARNESS_VALIDATION_FAILED" if not structure_ok else "CONFIGURED_PROVIDER_REQUIRED"
    report = {
        "schema_version": 1,
        "status": status,
        "project_name": name,
        "mode": resolved_mode,
        "delivery_profile": delivery,
        "detected": detected,
        "adapter_assessment": adapter,
        "provider_ready": provider_ready,
        "open_items": open_items,
        "writes": writes,
        "validation": validation,
        "next_commands": [
            "python sdlc/scripts/harness.py check --setup",
            "python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only",
        ],
    }
    result_path = root / "sdlc/runtime/setup/setup-result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bootstrap minimum executable SDLC Harness project configuration.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--name", default="project")
    ap.add_argument("--mode", default="AUTO")
    ap.add_argument("--delivery", default="STANDARD")
    ap.add_argument("--customer", default="MINIMAL")
    ap.add_argument("--reverse", default="DIRECT_ONLY")
    ap.add_argument("--provider-command", help="Quoted external Agent command using {context_path}/{result_path} placeholders")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = bootstrap(
            Path(args.root), name=args.name, mode=args.mode, delivery=args.delivery,
            customer=args.customer, reverse=args.reverse, provider_command=args.provider_command,
            force=args.force, validate=not args.no_validate,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "SETUP_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "READY_FOR_PLAN" else 4


if __name__ == "__main__":
    raise SystemExit(main())
