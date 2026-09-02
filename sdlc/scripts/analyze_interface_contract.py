#!/usr/bin/env python3
"""Bounded interface-contract analyzer for explicitly supplied OpenAPI/AsyncAPI/WSDL files.

The analyzer emits OBSERVED contract evidence only. It never infers that an interface is a
confirmed business requirement or relation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import yaml

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_structured(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def _ref_names(value: Any) -> list[str]:
    refs: set[str] = set()
    def walk(node: Any):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str):
                    refs.add(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(value)
    return sorted(refs)


def _openapi(doc: dict[str, Any]) -> dict[str, Any]:
    operations = []
    for path, path_item in (doc.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if str(method).lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operations.append({
                "transport": "HTTP",
                "method": str(method).upper(),
                "path": str(path),
                "operation_id": operation.get("operationId"),
                "summary": operation.get("summary"),
                "request_schema_refs": _ref_names(operation.get("requestBody") or {}),
                "response_schema_refs": _ref_names(operation.get("responses") or {}),
                "security": operation.get("security"),
            })
    servers = []
    for item in doc.get("servers") or []:
        if isinstance(item, dict) and item.get("url"):
            servers.append(str(item.get("url")))
    return {
        "contract_kind": "OPENAPI",
        "spec_version": doc.get("openapi") or doc.get("swagger"),
        "servers": servers,
        "operations": operations,
        "schema_refs": _ref_names(doc),
        "signals": ["rest_api", "external_interface", "schema_contract"],
    }


def _asyncapi(doc: dict[str, Any]) -> dict[str, Any]:
    channels = []
    for name, channel in (doc.get("channels") or {}).items():
        if not isinstance(channel, dict):
            continue
        ops = []
        for action in ("publish", "subscribe"):
            if isinstance(channel.get(action), dict):
                op = channel[action]
                ops.append({"action": action.upper(), "operation_id": op.get("operationId"), "message_refs": _ref_names(op.get("message") or {})})
        channels.append({"channel": str(name), "operations": ops})
    servers = sorted((doc.get("servers") or {}).keys()) if isinstance(doc.get("servers"), dict) else []
    return {
        "contract_kind": "ASYNCAPI",
        "spec_version": doc.get("asyncapi"),
        "servers": servers,
        "channels": channels,
        "schema_refs": _ref_names(doc),
        "signals": ["async_message", "external_interface", "schema_contract"],
    }


def _wsdl(path: Path) -> dict[str, Any]:
    root = ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
    operations = []
    services = []
    for elem in root.iter():
        local = elem.tag.split("}")[-1]
        if local == "operation" and elem.attrib.get("name"):
            operations.append(elem.attrib.get("name"))
        elif local == "service" and elem.attrib.get("name"):
            services.append(elem.attrib.get("name"))
    return {
        "contract_kind": "WSDL",
        "services": sorted(set(services)),
        "operations": sorted(set(operations)),
        "signals": ["external_interface", "schema_contract"],
    }


def analyze_file(path: Path, root: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    rel = path.relative_to(root).as_posix()
    base = {"path": rel, "sha256": _digest(path), "truth_state": "OBSERVED", "business_truth_confirmed": False}
    suffix = path.suffix.lower()
    try:
        if suffix in {".yaml", ".yml", ".json"}:
            doc = _load_structured(path)
            if not isinstance(doc, dict):
                return None, {"type": "INTERFACE_FORMAT_UNRECOGNIZED", "path": rel, "reason": "structured root is not an object"}
            if doc.get("openapi") or doc.get("swagger"):
                base.update(_openapi(doc)); return base, None
            if doc.get("asyncapi"):
                base.update(_asyncapi(doc)); return base, None
            return None, {"type": "INTERFACE_FORMAT_UNRECOGNIZED", "path": rel, "reason": "no OpenAPI/Swagger/AsyncAPI marker"}
        if suffix in {".wsdl", ".xml"}:
            data = _wsdl(path); base.update(data); return base, None
        return None, {"type": "INTERFACE_FORMAT_UNSUPPORTED", "path": rel, "reason": f"unsupported extension {suffix or '<none>'}"}
    except (ValueError, json.JSONDecodeError, yaml.YAMLError, ET.ParseError) as exc:
        return None, {"type": "INTERFACE_PARSE_FAILED", "path": rel, "reason": str(exc)}


def analyze(root: Path, files: list[str]) -> dict[str, Any]:
    root = root.resolve()
    evidence = []
    open_items = []
    for index, rel in enumerate(files, 1):
        path = (root / rel).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise ValueError(f"target escapes source root: {rel}")
        if not path.is_file():
            open_items.append({"open_id": f"OPEN-INTERFACE-{index:03d}", "type": "SOURCE_FILE_MISSING", "path": rel,
                               "blocks_reasoning": False, "blocks_action": False})
            continue
        item, problem = analyze_file(path, root)
        if item:
            evidence.append(item)
        if problem:
            open_items.append({"open_id": f"OPEN-INTERFACE-{index:03d}", **problem, "blocks_reasoning": False, "blocks_action": False})
    return {"schema_version": 1, "artifact_type": "SOURCE_ANALYSIS_RESULT", "source_analysis_result": {
        "analyzer_id": "interface-contract", "bounded": True, "requested_files": files, "evidence": evidence, "open_items": open_items,
        "truth_guards": {"source_behavior_is_not_business_truth": True, "interface_contract_is_evidence_not_requirement": True,
                         "name_similarity_does_not_confirm_trace": True}}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.source_root, args.file)
    text = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
