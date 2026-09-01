#!/usr/bin/env python3
"""Project-specific Java/Spring/MyBatis structural impact adapter pilot.

This adapter intentionally lives under sdlc/custom/project. It is not Core.
It provides deterministic static candidates for a narrow subset:
- Java class/method symbols and direct field.member(...) calls
- Spring mapping annotations when present
- Controller naming-convention entry-point candidates when annotations are absent
- MyBatis mapper namespace/statement symbols
- SQL table READS/WRITES lineage for common SELECT/INSERT/UPDATE/DELETE/MERGE forms
- CREATE TABLE assets from .sql schema files

It does NOT claim full Java semantic resolution, runtime wiring, reflection,
transaction propagation, external API/event/config/test/build coverage, or
business-impact confirmation. Missing evidence becomes a coverage gap.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ADAPTER_ID = "JAVA_SPRING_MYBATIS_STATIC_PILOT_V0_1"
COVERAGE_DIMENSIONS = [
    "ENTRY_POINT", "CALLER", "CALLEE", "DATA_READ_WRITE", "TRANSACTION",
    "EXTERNAL_INTERFACE", "EVENT", "CONFIG_FEATURE_FLAG", "TEST",
    "MODULE_BUILD_DEPENDENCY", "DYNAMIC_RUNTIME_GAP",
]

JAVA_CLASS_RE = re.compile(r"\b(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)")
PACKAGE_RE = re.compile(r"\bpackage\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*;")
FIELD_RE = re.compile(
    r"\b(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?"
    r"([A-Za-z_$][\w$]*(?:<[^;=]+>)?(?:\[\])?)\s+([A-Za-z_$][\w$]*)\s*(?:=[^;]*)?;"
)
METHOD_RE = re.compile(
    r"\b(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?"
    r"(?:<[^>{}]+>\s+)?([A-Za-z_$][\w$<>, ?\[\].]*)\s+"
    r"([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*(?:throws\s+[^\{]+)?\{"
)
MEMBER_CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\.([A-Za-z_$][\w$]*)\s*\(")
MAPPING_RE = re.compile(
    r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*"
    r"(?:\(([^)]*)\))?"
)
CREATE_TABLE_RE = re.compile(r"\bCREATE\s+TABLE\s+([A-Za-z0-9_.$\"]+)", re.I)
SELECT_TABLE_RE = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_.$\"]+)", re.I)
INSERT_TABLE_RE = re.compile(r"\bINSERT\s+INTO\s+([A-Za-z0-9_.$\"]+)", re.I)
UPDATE_TABLE_RE = re.compile(r"\bUPDATE\s+([A-Za-z0-9_.$\"]+)", re.I)
DELETE_TABLE_RE = re.compile(r"\bDELETE\s+FROM\s+([A-Za-z0-9_.$\"]+)", re.I)
MERGE_TABLE_RE = re.compile(r"\bMERGE\s+INTO\s+([A-Za-z0-9_.$\"]+)", re.I)


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _table_name(raw: str) -> str:
    return raw.strip().strip('"').upper()


def _balanced_body(text: str, open_brace_index: int) -> tuple[str, int]:
    depth = 0
    in_string = False
    quote = ""
    escaped = False
    for index in range(open_brace_index, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue
        if ch in {'"', "'"}:
            in_string = True
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index + 1:index], index
    return text[open_brace_index + 1:], len(text) - 1


def _annotations_before(text: str, method_start: int) -> list[dict]:
    prefix = text[max(0, method_start - 700):method_start]
    # Keep only the suffix after the previous method/class closing brace to reduce false association.
    suffix = prefix[prefix.rfind("}") + 1:]
    rows = []
    for match in MAPPING_RE.finditer(suffix):
        rows.append({"annotation": match.group(1), "arguments": (match.group(2) or "").strip()})
    return rows


def _symbol_id(fqcn: str, method: str) -> str:
    return f"symbol:{fqcn}#{method}"


def _entry_id(fqcn: str, method: str) -> str:
    return f"entry:{fqcn}#{method}"


def _mybatis_id(namespace: str, statement: str) -> str:
    return f"mybatis:{namespace}#{statement}"


def _data_id(table: str) -> str:
    return f"data:{table}"


def parse_java(root: Path) -> dict:
    classes = {}
    for path in sorted(root.rglob("*.java")):
        text = path.read_text(encoding="utf-8")
        package_match = PACKAGE_RE.search(text)
        class_match = JAVA_CLASS_RE.search(text)
        if not class_match:
            continue
        package = package_match.group(1) if package_match else ""
        class_name = class_match.group(1)
        fqcn = f"{package}.{class_name}" if package else class_name
        fields = {name: typ.split("<", 1)[0].replace("[]", "") for typ, name in FIELD_RE.findall(text)}
        methods = []
        for match in METHOD_RE.finditer(text):
            return_type, method_name, params = match.groups()
            body, end = _balanced_body(text, match.end() - 1)
            calls = [{"receiver": receiver, "method": method} for receiver, method in MEMBER_CALL_RE.findall(body)]
            methods.append({
                "name": method_name,
                "return_type": return_type.strip(),
                "params": params.strip(),
                "body": body,
                "calls": calls,
                "annotations": _annotations_before(text, match.start()),
                "start": match.start(),
                "end": end,
            })
        classes[fqcn] = {
            "fqcn": fqcn,
            "class_name": class_name,
            "package": package,
            "path": path,
            "relpath": _rel(root, path),
            "fields": fields,
            "methods": methods,
            "text": text,
        }
    return classes


def parse_mybatis(root: Path) -> dict:
    mappers = {}
    for path in sorted(root.rglob("*.xml")):
        try:
            xml_root = ET.fromstring(path.read_text(encoding="utf-8"))
        except (ET.ParseError, UnicodeDecodeError):
            continue
        if xml_root.tag.split("}")[-1] != "mapper" or not xml_root.attrib.get("namespace"):
            continue
        namespace = xml_root.attrib["namespace"]
        statements = {}
        for child in list(xml_root):
            tag = child.tag.split("}")[-1].lower()
            statement_id = child.attrib.get("id")
            if tag not in {"select", "insert", "update", "delete"} or not statement_id:
                continue
            sql = " ".join("".join(child.itertext()).split())
            statements[statement_id] = {"id": statement_id, "tag": tag, "sql": sql}
        mappers[namespace] = {
            "namespace": namespace,
            "path": path,
            "relpath": _rel(root, path),
            "statements": statements,
        }
    return mappers


def parse_schema(root: Path) -> dict[str, dict]:
    tables = {}
    for path in sorted(root.rglob("*.sql")):
        text = path.read_text(encoding="utf-8")
        for match in CREATE_TABLE_RE.finditer(text):
            table = _table_name(match.group(1))
            tables.setdefault(table, {"table": table, "path": path, "relpath": _rel(root, path)})
    return tables


def sql_lineage(sql: str, statement_tag: str) -> tuple[set[str], set[str]]:
    reads = {_table_name(x) for x in SELECT_TABLE_RE.findall(sql)}
    writes = set()
    writes.update(_table_name(x) for x in INSERT_TABLE_RE.findall(sql))
    writes.update(_table_name(x) for x in UPDATE_TABLE_RE.findall(sql))
    writes.update(_table_name(x) for x in DELETE_TABLE_RE.findall(sql))
    merge_targets = {_table_name(x) for x in MERGE_TABLE_RE.findall(sql)}
    writes.update(merge_targets)
    # MERGE must inspect target rows to decide MATCHED/NOT MATCHED.
    reads.update(merge_targets)
    reads.discard("DUAL")
    writes.discard("DUAL")
    if statement_tag == "select":
        writes.clear()
    return reads, writes


def analyze(source_root: Path) -> dict:
    source_root = source_root.resolve()
    classes = parse_java(source_root)
    mappers = parse_mybatis(source_root)
    schema_tables = parse_schema(source_root)

    nodes: dict[str, dict] = {}
    edges: dict[tuple[str, str, str], dict] = {}
    coverage_gaps = []
    unsupported_patterns = []

    def add_node(node: dict) -> None:
        nodes.setdefault(node["id"], node)

    def add_edge(edge: dict) -> None:
        key = (edge["from"], edge["type"], edge["to"])
        edges.setdefault(key, edge)

    # Schema assets first so SQL lineage can reuse stable DATA_ASSET nodes.
    for table, info in sorted(schema_tables.items()):
        add_node({
            "id": _data_id(table),
            "type": "DATA_ASSET",
            "locator": f"{info['relpath']}#{table}",
            "confidence": "HIGH",
            "status": "OBSERVED",
        })

    # MyBatis statement symbols and SQL lineage.
    for namespace, mapper in sorted(mappers.items()):
        for statement_id, statement in sorted(mapper["statements"].items()):
            statement_node = _mybatis_id(namespace, statement_id)
            add_node({
                "id": statement_node,
                "type": "SOURCE_SYMBOL",
                "locator": f"{mapper['relpath']}#{namespace}.{statement_id}",
                "confidence": "HIGH",
                "status": "OBSERVED",
            })
            reads, writes = sql_lineage(statement["sql"], statement["tag"])
            for table in sorted(reads | writes):
                data_node = _data_id(table)
                if data_node not in nodes:
                    add_node({
                        "id": data_node,
                        "type": "DATA_ASSET",
                        "locator": f"{mapper['relpath']}#{namespace}.{statement_id}:{table}",
                        "confidence": "MEDIUM",
                        "status": "CHECK_REQUIRED",
                    })
                if table in reads:
                    add_edge({
                        "from": statement_node,
                        "to": data_node,
                        "type": "READS",
                        "evidence": f"MyBatis SQL `{statement['sql']}`",
                        "confidence": "HIGH",
                        "status": "OBSERVED",
                    })
                if table in writes:
                    add_edge({
                        "from": statement_node,
                        "to": data_node,
                        "type": "WRITES",
                        "evidence": f"MyBatis SQL `{statement['sql']}`",
                        "confidence": "HIGH",
                        "status": "OBSERVED",
                    })

    simple_class = {item["class_name"]: fqcn for fqcn, item in classes.items()}
    mapper_simple = {namespace.rsplit(".", 1)[-1]: namespace for namespace in mappers}

    # Java symbols and entry points.
    for fqcn, cls in sorted(classes.items()):
        is_controller_name = cls["class_name"].endswith("Controller")
        for method in cls["methods"]:
            symbol = _symbol_id(fqcn, method["name"])
            add_node({
                "id": symbol,
                "type": "SOURCE_SYMBOL",
                "locator": f"{cls['relpath']}#{fqcn}.{method['name']}",
                "confidence": "HIGH",
                "status": "OBSERVED",
            })
            mappings = method["annotations"]
            if mappings:
                entry = _entry_id(fqcn, method["name"])
                add_node({
                    "id": entry,
                    "type": "ENTRY_POINT",
                    "locator": f"{cls['relpath']}#{fqcn}.{method['name']}",
                    "confidence": "HIGH",
                    "status": "OBSERVED",
                })
                add_edge({
                    "from": entry,
                    "to": symbol,
                    "type": "TRACES_TO",
                    "evidence": ", ".join(f"@{x['annotation']}({x['arguments']})" for x in mappings),
                    "confidence": "HIGH",
                    "status": "OBSERVED",
                })
            elif is_controller_name:
                entry = _entry_id(fqcn, method["name"])
                add_node({
                    "id": entry,
                    "type": "ENTRY_POINT",
                    "locator": f"{cls['relpath']}#{fqcn}.{method['name']}",
                    "confidence": "MEDIUM",
                    "status": "CHECK_REQUIRED",
                })
                add_edge({
                    "from": entry,
                    "to": symbol,
                    "type": "TRACES_TO",
                    "evidence": "Controller naming convention without Spring mapping annotation",
                    "confidence": "MEDIUM",
                    "status": "CHECK_REQUIRED",
                })

    # Direct member calls: caller -> callee and reverse CALLER edge.
    for fqcn, cls in sorted(classes.items()):
        for method in cls["methods"]:
            caller = _symbol_id(fqcn, method["name"])
            for call in method["calls"]:
                receiver_type = cls["fields"].get(call["receiver"])
                if not receiver_type:
                    continue
                target = None
                evidence = f"{call['receiver']}.{call['method']}(...) in {cls['relpath']}#{fqcn}.{method['name']}"
                confidence = "HIGH"
                status = "OBSERVED"
                if receiver_type in simple_class:
                    target = _symbol_id(simple_class[receiver_type], call["method"])
                    if target not in nodes:
                        target = None
                elif receiver_type in mapper_simple:
                    namespace = mapper_simple[receiver_type]
                    candidate = _mybatis_id(namespace, call["method"])
                    if candidate in nodes:
                        target = candidate
                if target:
                    add_edge({
                        "from": caller,
                        "to": target,
                        "type": "CALLEE",
                        "evidence": evidence,
                        "confidence": confidence,
                        "status": status,
                    })
                    add_edge({
                        "from": target,
                        "to": caller,
                        "type": "CALLER",
                        "evidence": evidence,
                        "confidence": confidence,
                        "status": status,
                    })

    entry_nodes = [n for n in nodes.values() if n["type"] == "ENTRY_POINT"]
    call_edges = [e for e in edges.values() if e["type"] in {"CALLER", "CALLEE"}]
    data_edges = [e for e in edges.values() if e["type"] in {"READS", "WRITES"}]
    test_files = sorted(_rel(source_root, p) for p in source_root.rglob("*") if p.is_file() and ("test" in p.name.lower() or "/test/" in "/" + _rel(source_root, p).lower()))
    build_files = sorted(_rel(source_root, p) for p in source_root.rglob("*") if p.is_file() and p.name in {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"})

    explicit_entry = any(n["type"] == "ENTRY_POINT" and n["status"] == "OBSERVED" for n in nodes.values())
    inferred_entry = any(n["type"] == "ENTRY_POINT" and n["status"] == "CHECK_REQUIRED" for n in nodes.values())
    if inferred_entry and not explicit_entry:
        coverage_gaps.append({
            "code": "SPRING_MAPPING_ANNOTATION_NOT_FOUND",
            "dimension": "ENTRY_POINT",
            "detail": "Controller naming convention produced entry-point candidates, but no Spring mapping annotation was observed.",
        })

    static_gaps = [
        ("TRANSACTION_BOUNDARY_NOT_CONFIRMED", "TRANSACTION", "@Transactional/transaction manager semantics are not resolved by this pilot."),
        ("EXTERNAL_INTERFACE_NOT_RESOLVED", "EXTERNAL_INTERFACE", "HTTP clients, Feign/WebClient/RestTemplate contracts are not resolved."),
        ("EVENT_WIRING_NOT_RESOLVED", "EVENT", "Kafka/JMS/event publication/subscription is not resolved."),
        ("CONFIG_FEATURE_FLAG_NOT_RESOLVED", "CONFIG_FEATURE_FLAG", "Spring configuration, profiles, feature flags and scheduler wiring are not resolved."),
        ("MODULE_BUILD_DEPENDENCY_NOT_RESOLVED", "MODULE_BUILD_DEPENDENCY", "Build/module dependency graph is not resolved."),
        ("DYNAMIC_DISPATCH_UNSUPPORTED", "DYNAMIC_RUNTIME_GAP", "Reflection, proxies, runtime bean selection and dynamic dispatch are outside static pilot coverage."),
    ]
    for code, dimension, detail in static_gaps:
        coverage_gaps.append({"code": code, "dimension": dimension, "detail": detail})

    if not test_files:
        coverage_gaps.append({"code": "TEST_COVERAGE_NOT_OBSERVED", "dimension": "TEST", "detail": "No test file was observed under the analyzed root."})
    if not build_files:
        coverage_gaps.append({"code": "BUILD_FILE_NOT_OBSERVED", "dimension": "MODULE_BUILD_DEPENDENCY", "detail": "No Maven/Gradle build file was observed under the analyzed root."})

    unsupported_patterns.extend([
        {"pattern": "reflection_dynamic_dispatch", "status": "UNSUPPORTED", "evidence": "Static regex/symbol candidate parser only"},
        {"pattern": "spring_proxy_runtime_wiring", "status": "UNSUPPORTED", "evidence": "No Spring container/runtime model"},
        {"pattern": "transaction_propagation", "status": "UNSUPPORTED", "evidence": "No transaction semantic engine"},
        {"pattern": "external_interface_contract_resolution", "status": "UNSUPPORTED", "evidence": "Not implemented in pilot"},
        {"pattern": "event_bus_resolution", "status": "UNSUPPORTED", "evidence": "Not implemented in pilot"},
    ])

    coverage = []
    for dimension in COVERAGE_DIMENSIONS:
        if dimension == "ENTRY_POINT":
            if explicit_entry:
                status, evidence = "COVERED", f"{len(entry_nodes)} entry point node(s); at least one mapping annotation observed"
            elif entry_nodes:
                status, evidence = "PARTIAL", f"{len(entry_nodes)} naming-convention candidate(s); annotation confirmation required"
            else:
                status, evidence = "GAP", "No entry point evidence observed"
        elif dimension in {"CALLER", "CALLEE"}:
            status = "COVERED" if call_edges else "GAP"
            evidence = f"{len(call_edges)} direct caller/callee edge(s); dynamic dispatch excluded" if call_edges else "No resolvable direct field-member calls"
        elif dimension == "DATA_READ_WRITE":
            status = "COVERED" if data_edges else "GAP"
            evidence = f"{len(data_edges)} MyBatis SQL data edge(s)" if data_edges else "No MyBatis table lineage observed"
        elif dimension == "TEST":
            status = "PARTIAL" if test_files else "GAP"
            evidence = f"Observed test-like files: {test_files}" if test_files else "No test files observed; test semantics not resolved"
        elif dimension == "MODULE_BUILD_DEPENDENCY":
            status = "PARTIAL" if build_files else "GAP"
            evidence = f"Observed build files: {build_files}; dependency graph not parsed" if build_files else "No build file observed; dependency graph not resolved"
        else:
            gap = next((g for g in coverage_gaps if g["dimension"] == dimension), None)
            status = "GAP" if gap else "PARTIAL"
            evidence = gap["detail"] if gap else "Checked only by narrow static pilot"
        coverage.append({"dimension": dimension, "status": status, "evidence_or_gap": evidence})

    project_context = {
        "language": "JAVA",
        "framework": "SPRING_STATIC_CANDIDATE",
        "persistence": ["MYBATIS"] if mappers else [],
        "source_root": str(source_root),
        "java_class_count": len(classes),
        "mybatis_mapper_count": len(mappers),
        "schema_table_count": len(schema_tables),
    }

    return {
        "adapter_id": ADAPTER_ID,
        "project_context": project_context,
        "nodes": [nodes[key] for key in sorted(nodes)],
        "edges": [edges[key] for key in sorted(edges)],
        "coverage": coverage,
        "coverage_gaps": coverage_gaps,
        "unsupported_patterns": unsupported_patterns,
        "completion_status": "PARTIAL_COVERAGE_GAPS",
        "business_impact_confirmed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Java/Spring/MyBatis project impact adapter pilot")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    root = Path(args.source_root)
    if not root.is_dir():
        parser.error(f"source root is not a directory: {root}")
    result = analyze(root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "adapter_id": result["adapter_id"],
        "nodes": len(result["nodes"]),
        "edges": len(result["edges"]),
        "coverage_gaps": len(result["coverage_gaps"]),
        "completion_status": result["completion_status"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
