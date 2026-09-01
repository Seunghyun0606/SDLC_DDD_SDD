#!/usr/bin/env python3
"""Extended Java/Spring Project Impact Adapter.

Builds on the stable Java/Spring/MyBatis pilot and adds conservative static candidates for
JPA repository/entity/table mapping, JDBC SQL, @Transactional, Feign/HTTP clients,
Kafka listeners/publication hints, @Scheduled and Spring config files. Every added relation
is heuristic/static and therefore PARTIAL; dynamic proxy/runtime semantics remain a gap.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("legacy_java_adapter", HERE / "java_spring_mybatis.py")
LEGACY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(LEGACY)

ADAPTER_ID = "JAVA_SPRING_ENTERPRISE_STATIC_V0_2"

ENTITY_RE = re.compile(r"@Entity\b", re.I)
TABLE_RE = re.compile(r"@Table\s*\([^)]*name\s*=\s*[\"']([^\"']+)[\"']", re.I)
REPOSITORY_RE = re.compile(r"(?:interface|class)\s+(\w+)\s+extends\s+[^\{]*(?:JpaRepository|CrudRepository|PagingAndSortingRepository)\s*<\s*(\w+)", re.I)
TRANSACTION_RE = re.compile(r"@Transactional\b(?:\s*\(([^)]*)\))?", re.I)
SCHEDULED_RE = re.compile(r"@Scheduled\s*\(([^)]*)\)", re.I)
KAFKA_LISTENER_RE = re.compile(r"@KafkaListener\s*\(([^)]*)\)", re.I)
FEIGN_RE = re.compile(r"@FeignClient\s*\(([^)]*)\)", re.I)
HTTP_CLIENT_RE = re.compile(r"\b(RestTemplate|WebClient|FeignClient|HttpClient)\b")
KAFKA_SEND_RE = re.compile(r"\b(?:KafkaTemplate|StreamBridge)\b|\.send\s*\(", re.I)
SQL_STRING_RE = re.compile(r"[\"']((?:SELECT|INSERT|UPDATE|DELETE|MERGE)\b.+?)[\"']", re.I | re.S)
CONFIG_FILE_RE = re.compile(r"application(?:-[^.]+)?\.(?:ya?ml|properties)$", re.I)


def _coverage_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["dimension"]: row for row in result.get("coverage", [])}


def _add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    nodes.setdefault(node["id"], node)


def _add_edge(edges: dict[tuple[str, str, str], dict[str, Any]], edge: dict[str, Any]) -> None:
    edges.setdefault((edge["from"], edge["type"], edge["to"]), edge)


def analyze(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    base = LEGACY.analyze(source_root)
    nodes = {row["id"]: dict(row) for row in base["nodes"]}
    edges = {(row["from"], row["type"], row["to"]): dict(row) for row in base["edges"]}
    gaps = [dict(row) for row in base["coverage_gaps"]]
    unsupported = [dict(row) for row in base["unsupported_patterns"]]
    coverage = _coverage_map(base)

    entity_tables: dict[str, str] = {}
    java_files = sorted(source_root.rglob("*.java"))
    transaction_count = 0
    external_count = 0
    event_count = 0
    config_count = 0

    for path in java_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = LEGACY._rel(source_root, path)
        package = LEGACY.PACKAGE_RE.search(text)
        cls_match = LEGACY.JAVA_CLASS_RE.search(text)
        if not cls_match:
            continue
        cls_name = cls_match.group(1)
        fqcn = f"{package.group(1)}.{cls_name}" if package else cls_name

        if ENTITY_RE.search(text):
            table = TABLE_RE.search(text)
            table_name = LEGACY._table_name(table.group(1)) if table else cls_name.upper()
            entity_tables[cls_name] = table_name
            data_id = LEGACY._data_id(table_name)
            _add_node(nodes, {
                "id": data_id, "type": "DATA_ASSET", "locator": f"{rel}#{cls_name}",
                "confidence": "MEDIUM" if not table else "HIGH", "status": "CHECK_REQUIRED" if not table else "OBSERVED",
            })

        repo = REPOSITORY_RE.search(text)
        if repo:
            repo_name, entity_name = repo.groups()
            repo_symbol = f"symbol:{fqcn}"
            _add_node(nodes, {"id": repo_symbol, "type": "SOURCE_SYMBOL", "locator": f"{rel}#{repo_name}", "confidence": "HIGH", "status": "OBSERVED"})
            table_name = entity_tables.get(entity_name, entity_name.upper())
            data_id = LEGACY._data_id(table_name)
            _add_node(nodes, {"id": data_id, "type": "DATA_ASSET", "locator": f"{rel}#{entity_name}", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})
            for kind in ["READS", "WRITES"]:
                _add_edge(edges, {
                    "from": repo_symbol, "to": data_id, "type": kind,
                    "evidence": f"Spring Data repository {repo_name}<{entity_name}>; CRUD direction requires method-level review",
                    "confidence": "MEDIUM", "status": "CHECK_REQUIRED",
                })

        methods = LEGACY._method_records(text)
        for method in methods:
            symbol = LEGACY._symbol_id(fqcn, method["name"])
            region = text[max(0, method["start"] - 1000):method["end"] + 1]
            tx = TRANSACTION_RE.search(region)
            if tx:
                transaction_count += 1
                _add_edge(edges, {
                    "from": symbol, "to": symbol, "type": "TRANSACTION",
                    "evidence": f"@Transactional({(tx.group(1) or '').strip()}) on/near {fqcn}.{method['name']}",
                    "confidence": "MEDIUM", "status": "CHECK_REQUIRED",
                })
            sched = SCHEDULED_RE.search(region)
            if sched:
                config_count += 1
                config_id = f"config:scheduled:{fqcn}#{method['name']}"
                _add_node(nodes, {"id": config_id, "type": "CONFIG", "locator": f"{rel}#{fqcn}.{method['name']}", "confidence": "HIGH", "status": "OBSERVED"})
                _add_edge(edges, {"from": symbol, "to": config_id, "type": "CONFIGURED_BY", "evidence": f"@Scheduled({sched.group(1)})", "confidence": "HIGH", "status": "OBSERVED"})
            kafka = KAFKA_LISTENER_RE.search(region)
            if kafka:
                event_count += 1
                event_id = f"event:kafka-listener:{fqcn}#{method['name']}"
                _add_node(nodes, {"id": event_id, "type": "EVENT", "locator": f"{rel}#{fqcn}.{method['name']}", "confidence": "HIGH", "status": "OBSERVED"})
                _add_edge(edges, {"from": event_id, "to": symbol, "type": "SUBSCRIBES", "evidence": f"@KafkaListener({kafka.group(1)})", "confidence": "HIGH", "status": "OBSERVED"})
            if KAFKA_SEND_RE.search(method.get("body", "")):
                event_count += 1
                event_id = f"event:kafka-publish:{fqcn}#{method['name']}"
                _add_node(nodes, {"id": event_id, "type": "EVENT", "locator": f"{rel}#{fqcn}.{method['name']}", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})
                _add_edge(edges, {"from": symbol, "to": event_id, "type": "PUBLISHES", "evidence": "KafkaTemplate/StreamBridge/send static hint", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})

            for sql_match in SQL_STRING_RE.finditer(method.get("body", "")):
                sql = " ".join(sql_match.group(1).split())
                reads, writes = LEGACY.sql_lineage(sql, "")
                for table in sorted(reads | writes):
                    data_id = LEGACY._data_id(table)
                    _add_node(nodes, {"id": data_id, "type": "DATA_ASSET", "locator": f"{rel}#{fqcn}.{method['name']}:{table}", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})
                    if table in reads:
                        _add_edge(edges, {"from": symbol, "to": data_id, "type": "READS", "evidence": f"JDBC SQL literal `{sql}`", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})
                    if table in writes:
                        _add_edge(edges, {"from": symbol, "to": data_id, "type": "WRITES", "evidence": f"JDBC SQL literal `{sql}`", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})

        feign = FEIGN_RE.search(text)
        if feign:
            external_count += 1
            ext_id = f"external:feign:{fqcn}"
            _add_node(nodes, {"id": ext_id, "type": "EXTERNAL_INTERFACE", "locator": f"{rel}#{fqcn}", "confidence": "HIGH", "status": "OBSERVED"})
        elif HTTP_CLIENT_RE.search(text):
            external_count += 1
            ext_id = f"external:http-client:{fqcn}"
            _add_node(nodes, {"id": ext_id, "type": "EXTERNAL_INTERFACE", "locator": f"{rel}#{fqcn}", "confidence": "MEDIUM", "status": "CHECK_REQUIRED"})

    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or not CONFIG_FILE_RE.search(path.name):
            continue
        rel = LEGACY._rel(source_root, path)
        config_count += 1
        _add_node(nodes, {"id": f"config:{rel}", "type": "CONFIG", "locator": rel, "confidence": "HIGH", "status": "OBSERVED"})

    data_edges = [e for e in edges.values() if e["type"] in {"READS", "WRITES"}]
    if data_edges and coverage["DATA_READ_WRITE"]["status"] == "GAP":
        coverage["DATA_READ_WRITE"] = {"dimension": "DATA_READ_WRITE", "status": "PARTIAL", "evidence_or_gap": f"{len(data_edges)} MyBatis/JPA/JDBC static lineage candidate(s)"}
    if transaction_count:
        coverage["TRANSACTION"] = {"dimension": "TRANSACTION", "status": "PARTIAL", "evidence_or_gap": f"{transaction_count} @Transactional candidate(s); propagation/runtime manager still unresolved"}
        gaps = [g for g in gaps if g.get("code") != "TRANSACTION_BOUNDARY_NOT_CONFIRMED"]
        gaps.append({"code": "TRANSACTION_RUNTIME_SEMANTICS_UNRESOLVED", "dimension": "TRANSACTION", "detail": "Annotations were observed but proxy/propagation/runtime manager semantics still require review."})
    if external_count:
        coverage["EXTERNAL_INTERFACE"] = {"dimension": "EXTERNAL_INTERFACE", "status": "PARTIAL", "evidence_or_gap": f"{external_count} Feign/HTTP client candidate(s) observed"}
        gaps = [g for g in gaps if g.get("code") != "EXTERNAL_INTERFACE_NOT_RESOLVED"]
        gaps.append({"code": "EXTERNAL_CONTRACT_PAYLOAD_RUNTIME_UNRESOLVED", "dimension": "EXTERNAL_INTERFACE", "detail": "Client candidates observed; payload/version/runtime destination need contract/tool evidence."})
    if event_count:
        coverage["EVENT"] = {"dimension": "EVENT", "status": "PARTIAL", "evidence_or_gap": f"{event_count} Kafka publish/subscribe candidate(s) observed"}
        gaps = [g for g in gaps if g.get("code") != "EVENT_WIRING_NOT_RESOLVED"]
        gaps.append({"code": "EVENT_RUNTIME_TOPOLOGY_UNRESOLVED", "dimension": "EVENT", "detail": "Static annotations/client hints observed; broker topology/schema/runtime binding need Tool evidence."})
    if config_count:
        coverage["CONFIG_FEATURE_FLAG"] = {"dimension": "CONFIG_FEATURE_FLAG", "status": "PARTIAL", "evidence_or_gap": f"{config_count} config/scheduler asset candidate(s) observed"}
        gaps = [g for g in gaps if g.get("code") != "CONFIG_FEATURE_FLAG_NOT_RESOLVED"]
        gaps.append({"code": "CONFIG_EFFECTIVE_VALUE_UNRESOLVED", "dimension": "CONFIG_FEATURE_FLAG", "detail": "Config assets observed; active profile/effective runtime value requires environment evidence."})

    unsupported_patterns = [row for row in unsupported if row.get("pattern") not in {"external_api_event_config_semantics", "transaction_propagation"}]
    unsupported_patterns.extend([
        {"pattern": "spring_transaction_runtime_propagation", "status": "PARTIAL_STATIC_ONLY"},
        {"pattern": "jpa_query_method_semantics", "status": "PARTIAL_STATIC_ONLY"},
        {"pattern": "stored_procedure_trigger_etl", "status": "UNSUPPORTED"},
        {"pattern": "live_broker_api_db_runtime_topology", "status": "TOOL_REQUIRED"},
    ])
    base.update({
        "adapter_id": ADAPTER_ID,
        "project_context": {
            **base["project_context"],
            "persistence": ["MyBatis XML", "JPA static candidate", "JDBC SQL literal candidate"],
            "external_static_candidates": external_count,
            "event_static_candidates": event_count,
        },
        "nodes": [nodes[k] for k in sorted(nodes)],
        "edges": [edges[k] for k in sorted(edges)],
        "coverage": [coverage[dimension] for dimension in LEGACY.COVERAGE_DIMENSIONS],
        "coverage_gaps": sorted(gaps, key=lambda x: (x.get("dimension", ""), x.get("code", ""))),
        "unsupported_patterns": sorted(unsupported_patterns, key=lambda x: x.get("pattern", "")),
        "completion_status": "PARTIAL_COVERAGE_GAPS",
        "business_impact_confirmed": False,
    })
    return base


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Extended Java/Spring static Project Impact Adapter")
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = Path(args.source_root)
    if not root.is_dir():
        print(f"ERROR: source root not found: {root}")
        return 2
    result = analyze(root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"adapter_id": result["adapter_id"], "nodes": len(result["nodes"]), "edges": len(result["edges"]), "coverage_gaps": len(result["coverage_gaps"]), "completion_status": result["completion_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
