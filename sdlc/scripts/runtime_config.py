#!/usr/bin/env python3
"""Runtime configuration resolver for the SDLC Harness.

New projects have one human-maintained entry point: ``.sdlc/project.yaml``.
Legacy ``sdlc/config/project-profile.yaml`` and ``source-profile.yaml`` remain readable only
for backward compatibility. Runtime consumers should call ``resolve_runtime_config`` rather
than asking a project user to understand multiple profile files.

The Harness intentionally supports only a conservative YAML subset so bootstrap/work/check do
not require PyYAML. Unknown user-config leaves are reported as DEAD_CONFIG instead of being
silently ignored.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

PROJECT_ENTRY_PATH = ".sdlc/project.yaml"
LEGACY_PROJECT_PROFILE_PATH = "sdlc/config/project-profile.yaml"
LEGACY_SOURCE_PROFILE_PATH = "sdlc/config/source-profile.yaml"

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

# Every leaf accepted in the human project entry must have an explicit owner.
# This list is deliberately small: adding a field without a consumer becomes DEAD_CONFIG.
RUNTIME_CONSUMED_PATHS = {
    "schema_version",
    "project.name",
    "project.mode",
    "delivery.profile",
    "technology.language",
    "technology.framework",
    "technology.build",
    "technology.test",
    "source.roots",
    "source.test_roots",
    "source.resource_roots",
    "source.excludes",
    "git.branch_strategy",
    "git.protected_branches",
    "documents.language",
    "unresolved",
}
RUNTIME_CONTEXT_PREFIXES = (
    "architecture.",
    "coding.",
    "data.",
    "interface.",
    "security.",
    "deployment.",
)
EXTENSION_PREFIXES = ("extensions.",)
DOCUMENT_ONLY_PATHS = {"project.description", "documents.customer_language"}


def _strip_comment(line: str) -> str:
    quoted = False
    quote = ""
    out = []
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
        pass
    return text


def load_yaml_subset(path: Path) -> dict[str, Any]:
    """Parse the subset used by Harness config; fail closed on malformed indentation."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending_list_keys: dict[int, tuple[dict[str, Any], str]] = {}

    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        clean = _strip_comment(raw)
        if not clean.strip():
            continue
        indent = len(clean) - len(clean.lstrip(" "))
        if indent % 2:
            raise ValueError(f"YAML indentation must use two-space levels: {path}:{number}")
        text = clean.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if text.startswith("- "):
            value = _scalar(text[2:])
            if not isinstance(parent, list):
                pending = pending_list_keys.get(stack[-1][0])
                if not pending:
                    raise ValueError(f"list item without list key: {path}:{number}")
                owner, key = pending
                owner[key] = []
                parent = owner[key]
                stack[-1] = (stack[-1][0], parent)
            parent.append(value)
            continue

        if ":" not in text or not isinstance(parent, dict):
            raise ValueError(f"unsupported YAML line: {path}:{number}: {text}")
        key, raw_value = text.split(":", 1)
        key = key.strip()
        value = _scalar(raw_value)
        if raw_value.strip() == "":
            parent[key] = {}
            pending_list_keys[indent] = (parent, key)
            stack.append((indent, parent[key]))
        else:
            parent[key] = value
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
    """Normalize build/test config into argv lists without invoking a shell."""
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
    # Lists are one configuration leaf. Their items are values, not independent keys.
    return [prefix] if prefix else []


def classify_project_config(project: dict[str, Any]) -> dict[str, list[str]]:
    result = {"runtime": [], "extension": [], "document": [], "dead": []}
    for path in sorted(set(_flatten_leaves(project))):
        if path in RUNTIME_CONSUMED_PATHS or any(path.startswith(prefix) for prefix in RUNTIME_CONTEXT_PREFIXES):
            result["runtime"].append(path)
        elif any(path.startswith(prefix) for prefix in EXTENSION_PREFIXES):
            result["extension"].append(path)
        elif path in DOCUMENT_ONLY_PATHS:
            result["document"].append(path)
        else:
            result["dead"].append(path)
    return result


def ensure_no_dead_config(project: dict[str, Any]) -> None:
    dead = classify_project_config(project)["dead"]
    if dead:
        raise ValueError("unused project config key(s): " + ", ".join(dead))


def compact_project_context(project: dict[str, Any]) -> dict[str, Any]:
    """Return only project facts useful to the Stage Agent; omit internal compatibility metadata."""
    keys = ["project", "technology", "architecture", "coding", "data", "interface", "security", "deployment", "documents", "unresolved"]
    return {key: project[key] for key in keys if key in project}


def legacy_to_project(project_profile: dict[str, Any], source_profile: dict[str, Any]) -> dict[str, Any]:
    """Map the runtime-consumed legacy subset into the single user-facing model."""
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
    """Build compatibility objects for old callers. These are derived, never the source of truth."""
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
    """Resolve one effective configuration, preferring ``.sdlc/project.yaml``.

    Returns both the unified project model and derived legacy-shaped objects so existing
    execution code can migrate incrementally without exposing those shapes to project users.
    """
    root = root.resolve()
    project_path = project_config_path or (root / PROJECT_ENTRY_PATH)
    if not project_path.is_absolute():
        project_path = root / project_path
    legacy_project = legacy_project_path or (root / LEGACY_PROJECT_PROFILE_PATH)
    legacy_source = legacy_source_path or (root / LEGACY_SOURCE_PROFILE_PATH)
    if not legacy_project.is_absolute():
        legacy_project = root / legacy_project
    if not legacy_source.is_absolute():
        legacy_source = root / legacy_source

    if project_path.is_file():
        project = load_config(project_path)
        if validate_usage:
            ensure_no_dead_config(project)
        source_kind = "PROJECT_ENTRY"
    else:
        legacy_project_data = load_config(legacy_project)
        legacy_source_data = load_config(legacy_source)
        if not legacy_project_data and not legacy_source_data:
            project = {}
            source_kind = "UNCONFIGURED"
        else:
            project = legacy_to_project(legacy_project_data, legacy_source_data)
            source_kind = "LEGACY_PROFILES"

    project_profile, source_profile = project_to_legacy_profiles(project) if project else ({}, {})
    return {
        "source_kind": source_kind,
        "user_config_path": project_path,
        "project": project,
        "project_profile": project_profile,
        "source_profile": source_profile,
        "usage": classify_project_config(project) if project else {"runtime": [], "extension": [], "document": [], "dead": []},
    }
