#!/usr/bin/env python3
"""Resolve the SDLC Harness project configuration.

Human-maintained entry point:
    .sdlc/project.yaml

Legacy project/source profiles remain readable for old projects, but new projects derive
machine compatibility profiles from the single project entry. Unknown leaves fail closed as
DEAD_CONFIG so a setting cannot silently pretend to be effective.

Agent execution is project-configurable but vendor-neutral:
- INTERACTIVE: the currently running IDE/CLI Agent performs the Stage work.
- HEADLESS: Harness launches a configured external Provider command.

When ``agent`` is omitted the default is INTERACTIVE. A previously configured legacy
``sdlc/config/agent-provider.json`` remains readable as a compatibility fallback so existing
automation projects are not silently switched to interactive execution.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

PROJECT_ENTRY_PATH = ".sdlc/project.yaml"
LEGACY_PROJECT_PROFILE_PATH = "sdlc/config/project-profile.yaml"
LEGACY_SOURCE_PROFILE_PATH = "sdlc/config/source-profile.yaml"
DEFAULT_PROVIDER_CONFIG_PATH = "sdlc/config/agent-provider.json"
EFFECTIVE_DIR = ".sdlc/runtime/effective"
AGENT_EXECUTION_MODES = {"INTERACTIVE", "HEADLESS"}

DELIVERY_PROFILES: dict[str, dict[str, Any]] = {
    "FAST": {
        "description": "XS/S 운영변경·소규모 기능용. 필요한 의미만 남기고 중간 산출물은 조건부로 수행한다.",
        "greenfield_stages": ["DECOMPOSE", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST"],
        "brownfield_stages": ["DECOMPOSE", "IMPACT", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST"],
        "optional_stages": ["CLARIFY", "PROCESS", "DISCOVERY", "VERIFY", "KNOWLEDGE_PROMOTION"],
        "graph_hops": 1,
        "program_readiness": "FAST",
        "customer_default": "MINIMAL",
        "reverse_default": "DIRECT_ONLY",
    },
    "STANDARD": {
        "description": "일반 SI/SM 기능용. 업무흐름·영향·설계·프로그램·검증을 균형 있게 수행한다.",
        "greenfield_stages": ["DECOMPOSE", "CLARIFY", "PROCESS", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY"],
        "brownfield_stages": ["DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY"],
        "optional_stages": ["KNOWLEDGE_PROMOTION"],
        "graph_hops": 3,
        "program_readiness": "STANDARD",
        "customer_default": "STANDARD",
        "reverse_default": "RELATED_GRAPH",
    },
    "FULL": {
        "description": "대형 구축·고위험 변경용. 전체 Stage와 지식승격 후보까지 사용한다.",
        "greenfield_stages": ["DECOMPOSE", "CLARIFY", "PROCESS", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION"],
        "brownfield_stages": ["DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION"],
        "optional_stages": [],
        "graph_hops": 4,
        "program_readiness": "FULL",
        "customer_default": "STANDARD",
        "reverse_default": "RELATED_GRAPH",
    },
}

# Leaves with a deterministic executable core consumer today.
RUNTIME_CONSUMED_PATHS = {
    "schema_version",
    "project.mode",
    "delivery.profile",
    "technology.build",
    "technology.test",
    "source.roots",
    "source.test_roots",
    "source.resource_roots",
    "git.protected_branches",
    "agent.execution",
    "agent.provider.id",
    "agent.provider.command",
    "agent.provider.timeout_seconds",
    "agent.provider.result_filename",
}
# These are passed to the Stage Agent as project context, but are not execution switches.
DOCUMENT_CONTEXT_PREFIXES = (
    "architecture.", "coding.", "data.", "interface.", "security.", "deployment.",
)
DOCUMENT_ONLY_PATHS = {
    "project.name",
    "project.description",
    "technology.language",
    "technology.framework",
    "source.excludes",
    "git.branch_strategy",
    "documents.language",
    "documents.customer_language",
    "unresolved",
}
EXTENSION_PREFIXES = ("extensions.",)


def _strip_comment(line: str) -> str:
    quoted = False
    quote = ""
    out: list[str] = []
    for ch in line:
        if ch in {"'", '"'}:
            if not quoted:
                quoted, quote = True, ch
            elif quote == ch:
                quoted, quote = False, ""
        if ch == "#" and not quoted:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "":
        return {}
    if text in {"null", "NULL", "~"}:
        return None
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    try:
        return int(text)
    except ValueError:
        return text


def load_yaml_subset(path: Path) -> dict[str, Any]:
    """Parse the conservative YAML subset used by Harness config."""
    lines = path.read_text(encoding="utf-8").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    index = 0
    while index < len(lines):
        number = index + 1
        raw = _strip_comment(lines[index])
        index += 1
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2:
            raise ValueError(f"YAML indentation must use two-space levels: {path}:{number}")
        text = raw.strip()
        if text.startswith("- "):
            raise ValueError(f"list item without a key: {path}:{number}")
        if ":" not in text:
            raise ValueError(f"unsupported YAML line: {path}:{number}: {text}")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError(f"invalid YAML indentation: {path}:{number}")
        parent = stack[-1][1]
        key, raw_value = text.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            parent[key] = _scalar(raw_value)
            continue

        look = index
        child_is_list = False
        while look < len(lines):
            candidate = _strip_comment(lines[look])
            if not candidate.strip():
                look += 1
                continue
            child_indent = len(candidate) - len(candidate.lstrip(" "))
            if child_indent <= indent:
                break
            child_is_list = candidate.strip().startswith("- ")
            break
        if child_is_list:
            values: list[Any] = []
            while index < len(lines):
                item_raw = _strip_comment(lines[index])
                if not item_raw.strip():
                    index += 1
                    continue
                item_indent = len(item_raw) - len(item_raw.lstrip(" "))
                if item_indent <= indent:
                    break
                if item_indent != indent + 2 or not item_raw.strip().startswith("- "):
                    raise ValueError(f"only scalar list items are supported: {path}:{index + 1}")
                values.append(_scalar(item_raw.strip()[2:]))
                index += 1
            parent[key] = values
        else:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"config object required: {path}")
        return data
    return load_yaml_subset(path)


def nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def project_mode(project: dict[str, Any]) -> str:
    value = str(nested(project, "project", "mode", default="AUTO") or "AUTO").upper()
    return value if value in {"GREENFIELD", "BROWNFIELD", "HYBRID", "AUTO"} else "AUTO"


def delivery_profile(project: dict[str, Any]) -> str:
    value = str(nested(project, "delivery", "profile", default="STANDARD") or "STANDARD").upper()
    return value if value in DELIVERY_PROFILES else "STANDARD"


def delivery_policy(project: dict[str, Any], *, resolved_mode: str | None = None) -> dict[str, Any]:
    profile = delivery_profile(project)
    mode = (resolved_mode or project_mode(project)).upper()
    if mode == "AUTO":
        mode = "BROWNFIELD"
    base = dict(DELIVERY_PROFILES[profile])
    base["profile"] = profile
    base["mode"] = mode
    base["enabled_stages"] = list(base["greenfield_stages"] if mode == "GREENFIELD" else base["brownfield_stages"])
    return base


def command_list(value: Any) -> list[list[str]]:
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        return [shlex.split(value)]
    if isinstance(value, list):
        result: list[list[str]] = []
        for row in value:
            if isinstance(row, str):
                result.append(shlex.split(row))
            elif isinstance(row, list) and row and all(isinstance(x, str) for x in row):
                result.append(row)
        return result
    return []


def provider_command(project: dict[str, Any]) -> list[str]:
    raw = nested(project, "agent", "provider", "command", default=[])
    if raw in (None, "", []):
        return []
    if isinstance(raw, str):
        return shlex.split(raw)
    if isinstance(raw, list) and all(isinstance(x, str) and x.strip() for x in raw):
        return [str(x) for x in raw]
    raise ValueError("agent.provider.command must be a command string or a list of non-empty strings")


def agent_execution_mode(project: dict[str, Any]) -> str:
    value = str(nested(project, "agent", "execution", default="INTERACTIVE") or "INTERACTIVE").upper()
    if value not in AGENT_EXECUTION_MODES:
        raise ValueError(f"unsupported agent.execution: {value}; expected INTERACTIVE or HEADLESS")
    return value


def resolve_agent_runtime(project: dict[str, Any], legacy_provider: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve interactive/headless execution while preserving enabled legacy Provider automation."""
    protected = list(nested(project, "git", "protected_branches", default=["main", "master"]) or ["main", "master"])
    explicit_agent = isinstance(project.get("agent"), dict)
    legacy = dict(legacy_provider or {})
    legacy_command = legacy.get("command")
    legacy_enabled = bool(
        not explicit_agent
        and legacy.get("enabled")
        and isinstance(legacy_command, list)
        and legacy_command
        and all(isinstance(x, str) and x for x in legacy_command)
    )
    if legacy_enabled:
        legacy["protected_branches"] = protected
        legacy.setdefault("schema_version", 1)
        legacy.setdefault("provider_class", "EXTERNAL_AGENT")
        legacy["execution_mode"] = "HEADLESS"
        return {
            "schema_version": 1,
            "execution_mode": "HEADLESS",
            "config_source": "LEGACY_PROVIDER_CONFIG",
            "provider_required": True,
            "ready": True,
            "provider_id": legacy.get("provider_id") or "LEGACY_AGENT_PROVIDER",
            "deprecation": "Move Provider settings to .sdlc/project.yaml agent.provider.*",
            "provider_config": legacy,
        }

    mode = agent_execution_mode(project)
    if mode == "INTERACTIVE":
        provider = {
            "schema_version": 1,
            "execution_mode": "INTERACTIVE",
            "provider_id": "CURRENT_INTERACTIVE_AGENT",
            "provider_class": "INTERACTIVE_AGENT",
            "enabled": False,
            "provider_required": False,
            "timeout_seconds": 0,
            "result_filename": "stage-result.json",
            "command": [],
            "protected_branches": protected,
            "allow_dirty_workspace": True,
            "allow_protected_branch_write": False,
            "allow_unverified_source_write": False,
        }
        return {
            "schema_version": 1,
            "execution_mode": "INTERACTIVE",
            "config_source": "PROJECT_DEFAULT" if not explicit_agent else "PROJECT_ENTRY",
            "provider_required": False,
            "ready": True,
            "provider_id": provider["provider_id"],
            "provider_config": provider,
        }

    command = provider_command(project)
    if not command:
        raise ValueError("agent.execution HEADLESS requires agent.provider.command")
    provider = {
        "schema_version": 1,
        "execution_mode": "HEADLESS",
        "provider_id": str(nested(project, "agent", "provider", "id", default="PROJECT_AGENT_PROVIDER") or "PROJECT_AGENT_PROVIDER"),
        "provider_class": "EXTERNAL_AGENT",
        "enabled": True,
        "timeout_seconds": int(nested(project, "agent", "provider", "timeout_seconds", default=180) or 180),
        "result_filename": str(nested(project, "agent", "provider", "result_filename", default="stage-result.json") or "stage-result.json"),
        "command": command,
        "protected_branches": protected,
        "allow_dirty_workspace": False,
        "allow_protected_branch_write": False,
        "allow_unverified_source_write": False,
    }
    return {
        "schema_version": 1,
        "execution_mode": "HEADLESS",
        "config_source": "PROJECT_ENTRY",
        "provider_required": True,
        "ready": True,
        "provider_id": provider["provider_id"],
        "provider_config": provider,
    }


def source_roots(config: dict[str, Any]) -> list[str]:
    roots: list[str] = []
    for key in ["roots", "test_roots", "resource_roots"]:
        value = nested(config, "source", key, default=[])
        if isinstance(value, list):
            roots.extend(str(x).rstrip("/") for x in value if str(x).strip())
    return sorted(set(roots))


def build_commands(config: dict[str, Any]) -> list[list[str]]:
    value = nested(config, "technology", "build", default=None)
    if value is None:
        value = nested(config, "build", "commands", default=[])
    return command_list(value)


def test_commands(config: dict[str, Any]) -> list[list[str]]:
    value = nested(config, "technology", "test", default=None)
    if value is None:
        value = nested(config, "test", "commands", default=[])
    return command_list(value)


def _flatten_leaves(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        rows: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_leaves(child, child_prefix))
        return rows
    return [prefix] if prefix else []


def classify_project_config(project: dict[str, Any]) -> dict[str, list[str]]:
    result = {"runtime": [], "extension": [], "document": [], "dead": []}
    for path in sorted(set(_flatten_leaves(project))):
        if path in RUNTIME_CONSUMED_PATHS:
            result["runtime"].append(path)
        elif any(path.startswith(prefix) for prefix in EXTENSION_PREFIXES):
            result["extension"].append(path)
        elif path in DOCUMENT_ONLY_PATHS or any(path.startswith(prefix) for prefix in DOCUMENT_CONTEXT_PREFIXES):
            result["document"].append(path)
        else:
            result["dead"].append(path)
    return result


def _validate_project_entry(project: dict[str, Any]) -> None:
    if project.get("schema_version") != 1:
        raise ValueError("project config schema_version must be 1")
    raw_mode = str(nested(project, "project", "mode", default="AUTO") or "AUTO").upper()
    if raw_mode not in {"GREENFIELD", "BROWNFIELD", "HYBRID", "AUTO"}:
        raise ValueError(f"unsupported project.mode: {raw_mode}")
    raw_delivery = str(nested(project, "delivery", "profile", default="STANDARD") or "STANDARD").upper()
    if raw_delivery not in DELIVERY_PROFILES:
        raise ValueError(f"unsupported delivery.profile: {raw_delivery}")
    for key in ["roots", "test_roots", "resource_roots", "excludes"]:
        value = nested(project, "source", key, default=[])
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError(f"source.{key} must be a list of strings")
    protected = nested(project, "git", "protected_branches", default=["main", "master"])
    if not isinstance(protected, list) or not all(isinstance(x, str) and x.strip() for x in protected):
        raise ValueError("git.protected_branches must be a list of non-empty strings")
    agent = project.get("agent")
    if agent is not None and not isinstance(agent, dict):
        raise ValueError("agent must be a mapping")
    mode = agent_execution_mode(project)
    provider = nested(project, "agent", "provider", default={})
    if provider not in ({}, None) and not isinstance(provider, dict):
        raise ValueError("agent.provider must be a mapping")
    if mode == "HEADLESS":
        if not provider_command(project):
            raise ValueError("agent.execution HEADLESS requires agent.provider.command")
        timeout = nested(project, "agent", "provider", "timeout_seconds", default=180)
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("agent.provider.timeout_seconds must be a positive integer")
    elif isinstance(provider, dict) and provider:
        raise ValueError("agent.provider settings are only valid when agent.execution is HEADLESS")


def ensure_no_dead_config(project: dict[str, Any]) -> None:
    dead = classify_project_config(project)["dead"]
    if dead:
        raise ValueError("unused project config key(s): " + ", ".join(dead))


def compact_project_context(project: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "project", "technology", "source", "architecture", "git", "coding", "data",
        "interface", "security", "deployment", "documents", "unresolved",
    ]
    return {key: project[key] for key in keys if key in project}


def legacy_to_project(project_profile: dict[str, Any], source_profile: dict[str, Any]) -> dict[str, Any]:
    project: dict[str, Any] = {
        "schema_version": 1,
        "project": {
            "name": nested(project_profile, "project", "name", default="project"),
            "mode": project_mode(project_profile),
        },
        "delivery": {"profile": delivery_profile(project_profile)},
        "technology": {
            "language": nested(project_profile, "technology", "language", default="OPEN"),
            "framework": nested(project_profile, "technology", "framework", default="OPEN"),
            "build": nested(source_profile, "build", "commands", default=[]),
            "test": nested(source_profile, "test", "commands", default=[]),
        },
        "source": {
            "roots": nested(source_profile, "source", "roots", default=[]),
            "test_roots": nested(source_profile, "source", "test_roots", default=[]),
            "resource_roots": nested(source_profile, "source", "resource_roots", default=[]),
            "excludes": nested(source_profile, "source", "excludes", default=[]),
        },
        "git": {
            "branch_strategy": "PROJECT_DEFINED",
            "protected_branches": nested(project_profile, "workflow", "protected_branches", default=["main", "master"]),
        },
        "documents": {"language": nested(project_profile, "documents", "language", default="ko-KR")},
        "unresolved": [],
    }
    database = nested(project_profile, "technology", "database", default=None)
    if database is not None:
        project["data"] = {"database": database}
    return project


def project_to_legacy_profiles(project: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    project_profile = {
        "project": {
            "name": nested(project, "project", "name", default="project"),
            "mode": project_mode(project),
        },
        "delivery": {"profile": delivery_profile(project)},
        "technology": {
            "language": nested(project, "technology", "language", default="OPEN"),
            "framework": nested(project, "technology", "framework", default="OPEN"),
            "database": nested(project, "data", "database", default="OPEN"),
        },
        "documents": {"language": nested(project, "documents", "language", default="ko-KR")},
        "workflow": {
            "execution_guard_enabled": True,
            "protected_branches": nested(project, "git", "protected_branches", default=["main", "master"]),
        },
        "project_context": compact_project_context(project),
    }
    source_profile = {
        "schema_version": 1,
        "source": {
            "roots": nested(project, "source", "roots", default=[]),
            "test_roots": nested(project, "source", "test_roots", default=[]),
            "resource_roots": nested(project, "source", "resource_roots", default=[]),
            "excludes": nested(project, "source", "excludes", default=[]),
            "existing_assets_first": True,
            "static_analysis_first": True,
            "full_repository_llm_scan": False,
        },
        "build": {"commands": nested(project, "technology", "build", default=[])},
        "test": {"commands": nested(project, "technology", "test", default=[])},
    }
    return project_profile, source_profile


def resolve_runtime_config(
    root: Path,
    *,
    project_config_path: Path | None = None,
    legacy_project_path: Path | None = None,
    legacy_source_path: Path | None = None,
    validate_usage: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    project_path = project_config_path or (root / PROJECT_ENTRY_PATH)
    legacy_project = legacy_project_path or (root / LEGACY_PROJECT_PROFILE_PATH)
    legacy_source = legacy_source_path or (root / LEGACY_SOURCE_PROFILE_PATH)
    if not project_path.is_absolute():
        project_path = root / project_path
    if not legacy_project.is_absolute():
        legacy_project = root / legacy_project
    if not legacy_source.is_absolute():
        legacy_source = root / legacy_source

    if project_path.is_file():
        project = load_config(project_path)
        _validate_project_entry(project)
        if validate_usage:
            ensure_no_dead_config(project)
        source_kind = "PROJECT_ENTRY"
    else:
        old_project = load_config(legacy_project)
        old_source = load_config(legacy_source)
        if not old_project and not old_source:
            project = {}
            source_kind = "UNCONFIGURED"
        else:
            project = legacy_to_project(old_project, old_source)
            source_kind = "LEGACY_PROFILES"

    project_profile, source_profile = project_to_legacy_profiles(project) if project else ({}, {})
    return {
        "source_kind": source_kind,
        "user_config_path": project_path,
        "project": project,
        "project_context": compact_project_context(project) if project else {},
        "project_profile": project_profile,
        "source_profile": source_profile,
        "agent_execution_mode": agent_execution_mode(project) if project else "INTERACTIVE",
        "usage": classify_project_config(project) if project else {"runtime": [], "extension": [], "document": [], "dead": []},
    }


def materialize_effective_profiles(
    root: Path,
    resolved: dict[str, Any] | None = None,
    *,
    provider_config_path: Path | None = None,
) -> dict[str, Path]:
    """Write machine-only artifacts consumed by work/change executors and Stage Agents."""
    root = root.resolve()
    resolved = resolved or resolve_runtime_config(root)
    if resolved.get("source_kind") == "UNCONFIGURED":
        raise ValueError("project configuration is missing")
    effective = root / EFFECTIVE_DIR
    effective.mkdir(parents=True, exist_ok=True)
    project_path = effective / "project-profile.json"
    source_path = effective / "source-profile.json"
    context_path = effective / "project-context.json"
    usage_path = effective / "config-usage.json"
    project_path.write_text(json.dumps(resolved["project_profile"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_path.write_text(json.dumps(resolved["source_profile"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    context_path.write_text(json.dumps(resolved["project_context"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    usage_path.write_text(json.dumps(resolved["usage"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths = {
        "project_profile": project_path,
        "source_profile": source_path,
        "project_context": context_path,
        "config_usage": usage_path,
    }

    base_provider = provider_config_path or (root / DEFAULT_PROVIDER_CONFIG_PATH)
    if not base_provider.is_absolute():
        base_provider = root / base_provider
    legacy_provider = load_config(base_provider) if base_provider.is_file() else {}
    agent_runtime = resolve_agent_runtime(resolved["project"], legacy_provider=legacy_provider)

    execution_path = effective / "agent-execution.json"
    execution_view = {key: value for key, value in agent_runtime.items() if key != "provider_config"}
    execution_path.write_text(json.dumps(execution_view, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["agent_execution"] = execution_path

    provider = dict(agent_runtime["provider_config"])
    protected = nested(resolved["project"], "git", "protected_branches", default=None)
    if protected is not None:
        provider["protected_branches"] = list(protected)
    provider_path = effective / "agent-provider.json"
    provider_path.write_text(json.dumps(provider, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["provider_config"] = provider_path
    return paths
