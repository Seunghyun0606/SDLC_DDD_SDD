#!/usr/bin/env python3
"""Small dependency-free runtime configuration helper.

Human-maintained project/source profiles stay YAML. The runtime only needs a conservative
subset of YAML (mappings, scalar lists and simple nested objects), so the Harness does not
require PyYAML just to bootstrap or execute. JSON is also accepted.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Any

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
    """Parse the subset used by Harness profiles; fail closed on malformed indentation."""
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


def source_roots(source_profile: dict[str, Any]) -> list[str]:
    roots: list[str] = []
    for key in ["roots", "test_roots", "resource_roots"]:
        value = nested(source_profile, "source", key, default=[])
        if isinstance(value, list):
            roots.extend(str(x).rstrip("/") for x in value if str(x).strip())
    return sorted(set(roots))
