#!/usr/bin/env python3
"""Executable first-use setup with one human-maintained project configuration.

New project users edit only ``.sdlc/project.yaml``. Legacy project/source profiles are derived
machine snapshots for backward compatibility. Missing technical facts are recorded as
``unresolved``; setup never invents Business Truth.

Agent execution defaults to INTERACTIVE. A Provider is required only when HEADLESS execution is
selected explicitly or an enabled legacy Provider is connected for backward compatibility.
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
            framework = "Spring"
            signals.append("SPRING")
        if re.search(r"mybatis", text, re.I):
            signals.append("MYBATIS")
        if re.search(r"spring-data-jpa|hibernate|jakarta\.persistence|javax\.persistence", text, re.I):
            signals.append("JPA")
            gaps.append("JPA 정밀 relation/runtime semantics는 정적 후보 이후 검토 필요")
        if re.search(r"kafka", text, re.I):
            signals.append("KAFKA")
            gaps.append("Kafka runtime topology/schema는 Tool Evidence 필요")
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
            if re.search(marker, text):
                framework = name
                break
        build_commands, test_commands = ["npm run build"], ["npm test -- --runInBand"]
        gaps.append("JavaScript/TypeScript Source relation Adapter는 현재 포함되지 않음")
    elif pyproject.is_file() or _project_python_exists(root, source_roots):
        language = "Python"
        if (root / "tests").exists():
            test_commands = ["python -m pytest"]
        gaps.append("Python Source relation Adapter는 현재 포함되지 않음")

    schema_files = list(root.rglob("schema.sql"))[:20] + list(root.rglob("*.ddl"))[:20]
    if schema_files:
        database = "SQL_SCHEMA_PRESENT"
        signals.append("DB_SCHEMA_FILE")

    brownfield = bool(source_roots or pom.is_file() or gradle or package.is_file() or pyproject.is_file() or schema_files)
    return {
        "detected_mode": "BROWNFIELD" if brownfield else "GREENFIELD",
        "language": language,
        "framework": framework,
        "database": database,
        "source_roots": source_roots,
        "test_roots": test_roots,
        "resource_roots": resource_roots,
        "build_commands": build_commands,
        "test_commands": test_commands,
        "signals": sorted(set(signals)),
        "coverage_gaps": gaps,
    }


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _yaml_dump(data: dict[str, Any]) -> str:
    lines: list[str] = []

    def emit(value: Any, indent: int) -> None:
        prefix = " " * indent
        if not isinstance(value, dict):
            raise ValueError("top-level config must be a mapping")
        for key, child in value.items():
            if isinstance(child, dict):
                lines.append(f"{prefix}{key}:")
                emit(child, indent + 2)
            elif isinstance(child, list):
                if not child:
                    lines.append(f"{prefix}{key}: []")
                else:
                    lines.append(f"{prefix}{key}:")
                    for item in child:
                        if isinstance(item, (dict, list)):
                            raise ValueError("project config supports scalar list items only")
                        lines.append(f"{prefix}  - {_yaml_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(child)}")

    emit(data, 0)
    return "\n".join(lines) + "\n"


def _new_project_model(name: str, mode: str, delivery: str, detected: dict[str, Any]) -> dict[str, Any]:
    unresolved: list[str] = []
    for key, label in [("language", "technology.language"), ("framework", "technology.framework"), ("database", "data.database")]:
        if detected[key] == "OPEN":
            unresolved.append(label)
    if mode in {"BROWNFIELD", "HYBRID"} and not detected["source_roots"]:
        unresolved.append("source.roots")
    if detected["source_roots"] and not detected["build_commands"] and not detected["test_commands"]:
        unresolved.append("technology.build/test")
    return {
        "schema_version": 1,
        "project": {"name": name, "mode": mode},
        "delivery": {"profile": delivery},
        "technology": {
            "language": detected["language"],
            "framework": detected["framework"],
            "build": detected["build_commands"],
            "test": detected["test_commands"],
        },
        "source": {
            "roots": detected["source_roots"],
            "test_roots": detected["test_roots"],
            "resource_roots": detected["resource_roots"],
            "excludes": [".git/**", "build/**", "target/**", "node_modules/**"],
        },
        "data": {"database": detected["database"]},
        "git": {"branch_strategy": "PROJECT_DEFINED", "protected_branches": ["main", "master"]},
        "documents": {"language": "ko-KR"},
        "unresolved": unresolved,
    }


def _machine_snapshot(data: dict[str, Any], source: str) -> str:
    return (
        "# MACHINE-GENERATED COMPATIBILITY SNAPSHOT - DO NOT EDIT\n"
        f"# Source of truth: {source}\n"
        "# Regenerated by sdlc/scripts/bootstrap_project.py\n"
        + _yaml_dump(data)
    )


def _project_yaml(name: str, mode: str, delivery: str, customer: str, reverse: str, d: dict[str, Any]) -> str:
    """Backward-compatible helper name; now returns the single project entry model."""
    return _yaml_dump(_new_project_model(name, mode, delivery, d))


def _source_yaml(d: dict[str, Any]) -> str:
    """Backward-compatible helper for tests/tools that still expect a source-profile shape."""
    project = _new_project_model("project", d["detected_mode"], "STANDARD", d)
    return _yaml_dump(CONFIG.project_to_legacy_profiles(project)[1])


def _provider(command_text: str | None, protected_branches: list[str] | None = None) -> dict[str, Any]:
    command = shlex.split(command_text) if command_text else []
    return {
        "schema_version": 1,
        "provider_id": "PROJECT_AGENT_PROVIDER" if command else "UNCONFIGURED_PROVIDER",
        "provider_class": "EXTERNAL_AGENT" if command else "UNCONFIGURED",
        "enabled": bool(command),
        "timeout_seconds": 180,
        "result_filename": "stage-result.json",
        "command": command,
        "protected_branches": list(protected_branches or ["main", "master"]),
        "allow_dirty_workspace": False,
        "allow_protected_branch_write": False,
        "allow_unverified_source_write": False,
    }


def bootstrap(
    root: Path,
    *,
    name: str,
    mode: str = "AUTO",
    delivery: str = "STANDARD",
    customer: str = "MINIMAL",
    reverse: str = "DIRECT_ONLY",
    provider_command: str | None = None,
    force: bool = False,
    validate: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    detected = _detect(root)
    resolved_mode = detected["detected_mode"] if mode.upper() == "AUTO" else mode.upper()
    if resolved_mode not in {"GREENFIELD", "BROWNFIELD", "HYBRID"}:
        raise ValueError("mode must be AUTO/GREENFIELD/BROWNFIELD/HYBRID")
    delivery = delivery.upper()
    if delivery not in CONFIG.DELIVERY_PROFILES:
        raise ValueError("delivery must be FAST/STANDARD/FULL")

    paths = {
        "entry": root / CONFIG.PROJECT_ENTRY_PATH,
        "legacy_project": root / CONFIG.LEGACY_PROJECT_PROFILE_PATH,
        "legacy_source": root / CONFIG.LEGACY_SOURCE_PROFILE_PATH,
        "provider": root / CONFIG.DEFAULT_PROVIDER_CONFIG_PATH,
        "store": root / "sdlc/canonical/store.json",
    }
    writes: dict[str, str] = {}

    def write_user(path: Path, content: str) -> str:
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        if existed and not force:
            return "EXISTING_KEPT"
        path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        return "UPDATED" if existed else "CREATED"

    def write_machine(path: Path, content: str) -> str:
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        return "REGENERATED" if existed else "CREATED"

    if paths["entry"].is_file() and not force:
        writes[CONFIG.PROJECT_ENTRY_PATH] = "EXISTING_KEPT"
    elif not paths["entry"].exists() and paths["legacy_project"].is_file() and paths["legacy_source"].is_file() and not force:
        migrated = CONFIG.legacy_to_project(CONFIG.load_config(paths["legacy_project"]), CONFIG.load_config(paths["legacy_source"]))
        migrated["project"]["name"] = name or migrated["project"].get("name", "project")
        paths["entry"].parent.mkdir(parents=True, exist_ok=True)
        paths["entry"].write_text(_yaml_dump(migrated), encoding="utf-8")
        writes[CONFIG.PROJECT_ENTRY_PATH] = "MIGRATED_FROM_LEGACY"
    else:
        project = _new_project_model(name, resolved_mode, delivery, detected)
        writes[CONFIG.PROJECT_ENTRY_PATH] = write_user(paths["entry"], _yaml_dump(project))

    resolved = CONFIG.resolve_runtime_config(root)
    if resolved["source_kind"] != "PROJECT_ENTRY":
        raise ValueError(".sdlc/project.yaml did not become the effective project configuration")
    project = resolved["project"]
    resolved_mode = CONFIG.project_mode(project)
    delivery = CONFIG.delivery_profile(project)
    if resolved["usage"]["dead"]:
        raise ValueError("dead config remains in project entry: " + ", ".join(resolved["usage"]["dead"]))

    legacy_project, legacy_source = resolved["project_profile"], resolved["source_profile"]
    writes[CONFIG.LEGACY_PROJECT_PROFILE_PATH] = write_machine(
        paths["legacy_project"], _machine_snapshot(legacy_project, CONFIG.PROJECT_ENTRY_PATH)
    )
    writes[CONFIG.LEGACY_SOURCE_PROFILE_PATH] = write_machine(
        paths["legacy_source"], _machine_snapshot(legacy_source, CONFIG.PROJECT_ENTRY_PATH)
    )

    desired_provider = _provider(provider_command, CONFIG.nested(project, "git", "protected_branches", default=["main", "master"]))
    provider_status = write_user(paths["provider"], json.dumps(desired_provider, ensure_ascii=False, indent=2) + "\n")
    writes[CONFIG.DEFAULT_PROVIDER_CONFIG_PATH] = provider_status
    provider = json.loads(paths["provider"].read_text(encoding="utf-8"))

    effective_paths = CONFIG.materialize_effective_profiles(root, resolved, provider_config_path=paths["provider"])
    for key, path in effective_paths.items():
        writes[path.relative_to(root).as_posix()] = "MACHINE_GENERATED"

    if not paths["store"].exists():
        APPLY.save_store(paths["store"], APPLY.empty_store())
        writes["sdlc/canonical/store.json"] = "CREATED"
    else:
        writes["sdlc/canonical/store.json"] = "EXISTING_KEPT"

    # Behavioral round-trip: the user entry controls delivery/source/build/test, not the snapshots.
    check = CONFIG.resolve_runtime_config(root)
    if CONFIG.project_mode(check["project"]) != resolved_mode or CONFIG.delivery_profile(check["project"]) != delivery:
        raise ValueError("project entry did not round-trip")
    if CONFIG.source_roots(check["source_profile"]) != CONFIG.source_roots(resolved["source_profile"]):
        raise ValueError("source roots did not round-trip from project entry")
    if CONFIG.build_commands(check["project"]) != CONFIG.build_commands(resolved["project"]):
        raise ValueError("build commands did not round-trip from project entry")
    if CONFIG.test_commands(check["project"]) != CONFIG.test_commands(resolved["project"]):
        raise ValueError("test commands did not round-trip from project entry")

    validation = None
    validator = root / "sdlc/scripts/validate_harness_structure.py"
    if validate and validator.is_file():
        cp = subprocess.run(
            [os.environ.get("PYTHON", "python"), str(validator), str(root)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        validation = {"exit_code": cp.returncode, "stdout": cp.stdout[-4000:], "stderr": cp.stderr[-4000:]}
    structure_ok = validation is None or validation["exit_code"] == 0

    agent_runtime = CONFIG.resolve_agent_runtime(project, legacy_provider=provider)
    execution_ready = bool(agent_runtime.get("ready"))
    execution_mode = str(agent_runtime.get("execution_mode") or "INTERACTIVE")
    provider_ready = bool(execution_mode == "HEADLESS" and execution_ready)

    adapter = "NONE"
    if resolved_mode in {"BROWNFIELD", "HYBRID"}:
        if detected["language"] == "Java" and "SPRING" in detected["signals"]:
            adapter = (
                "JAVA_SPRING_ENTERPRISE_STATIC_V0_2"
                if any(x in detected["signals"] for x in ["JPA", "KAFKA"]) or "MYBATIS" not in detected["signals"]
                else "JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1"
            )
        else:
            adapter = "PROJECT_ADAPTER_REQUIRED_OR_CORE_PARTIAL"

    opens = [str(x) for x in CONFIG.nested(project, "unresolved", default=[]) if str(x).strip()]
    if execution_mode == "HEADLESS" and not execution_ready:
        opens.append("실제 Agent Provider command")
    status = (
        "READY_FOR_PLAN"
        if execution_ready and structure_ok
        else "HARNESS_VALIDATION_FAILED"
        if not structure_ok
        else "AGENT_EXECUTION_CONFIG_REQUIRED"
    )
    report = {
        "schema_version": 3,
        "status": status,
        "project_name": CONFIG.nested(project, "project", "name", default=name),
        "mode": resolved_mode,
        "delivery_profile": delivery,
        "user_config": CONFIG.PROJECT_ENTRY_PATH,
        "runtime_config_source": check["source_kind"],
        "config_usage": check["usage"],
        "agent_execution": {
            "mode": execution_mode,
            "ready": execution_ready,
            "provider_required": bool(agent_runtime.get("provider_required")),
            "provider_id": agent_runtime.get("provider_id"),
            "config_source": agent_runtime.get("config_source"),
            "deprecation": agent_runtime.get("deprecation"),
        },
        "legacy_profiles": {
            "role": "MACHINE_GENERATED_COMPATIBILITY_ONLY",
            "project": CONFIG.LEGACY_PROJECT_PROFILE_PATH,
            "source": CONFIG.LEGACY_SOURCE_PROFILE_PATH,
        },
        "legacy_setup_options": {
            "customer": customer,
            "reverse": reverse,
            "note": "kept for CLI compatibility; no longer create user-maintained profile fields",
        },
        "detected": detected,
        "adapter_assessment": adapter,
        "provider_ready": provider_ready,
        "open_items": sorted(set(opens)),
        "writes": writes,
        "validation": validation,
        "next_commands": ["python sdlc/scripts/harness.py check --setup", "python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only"],
    }
    result_path = root / "sdlc/runtime/setup/setup-result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bootstrap the single user-facing SDLC Harness project configuration.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--name", default="project")
    ap.add_argument("--mode", default="AUTO")
    ap.add_argument("--delivery", default="STANDARD")
    ap.add_argument("--customer", default="MINIMAL", help="legacy CLI compatibility option")
    ap.add_argument("--reverse", default="DIRECT_ONLY", help="legacy CLI compatibility option")
    ap.add_argument("--provider-command")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = bootstrap(
            Path(args.root),
            name=args.name,
            mode=args.mode,
            delivery=args.delivery,
            customer=args.customer,
            reverse=args.reverse,
            provider_command=args.provider_command,
            force=args.force,
            validate=not args.no_validate,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "SETUP_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "READY_FOR_PLAN" else 4


if __name__ == "__main__":
    raise SystemExit(main())
