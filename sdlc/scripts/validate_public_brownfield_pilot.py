#!/usr/bin/env python3
"""Run the Project Impact Adapter against a pinned real public repository snapshot.

This is an integration pilot, not a claim of production completeness. The validator
checks a few source-grounded relations and explicitly records known static-analysis gaps.
A public source repository has no customer-confirmed Business Truth, so this pilot also
records that Brownfield Reconciliation empirical validation is still NOT_RUN.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_PATH = ROOT / "sdlc/custom/project/adapters/impact/java_spring_mybatis.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("java_spring_mybatis_public_pilot", ADAPTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def validate(source_root: Path, repository: str, commit: str) -> dict[str, Any]:
    adapter = _load_adapter()
    impact = adapter.analyze(source_root)
    nodes = {row["id"]: row for row in impact["nodes"]}
    edges = {(row["from"], row["type"], row["to"]): row for row in impact["edges"]}

    controller_entry = "entry:com.macro.mall.controller.OmsOrderController#list"
    controller_symbol = "symbol:com.macro.mall.controller.OmsOrderController#list"
    service_impl_symbol = "symbol:com.macro.mall.service.impl.OmsOrderServiceImpl#list"
    mapper_symbol = "mybatis:com.macro.mall.dao.OmsOrderDao#getList"
    order_table = "data:OMS_ORDER"

    checks = {
        "controller_entry_observed": controller_entry in nodes,
        "controller_symbol_observed": controller_symbol in nodes,
        "service_impl_symbol_observed": service_impl_symbol in nodes,
        "mybatis_statement_observed": mapper_symbol in nodes,
        "service_to_mybatis_callee_observed": (service_impl_symbol, "CALLEE", mapper_symbol) in edges,
        "mybatis_reads_order_table": (mapper_symbol, "READS", order_table) in edges,
    }
    failures = [name for name, passed in checks.items() if not passed]

    # Current static pilot cannot resolve a Controller field typed as an interface to
    # its Spring implementation. Record this as a real-world limitation, not as no impact.
    controller_to_impl = (controller_symbol, "CALLEE", service_impl_symbol) in edges
    real_world_gaps = []
    if not controller_to_impl:
        real_world_gaps.append({
            "code": "JAVA_INTERFACE_IMPLEMENTATION_RESOLUTION_REQUIRED",
            "dimension": "CALLEE",
            "detail": "Controller field type OmsOrderService is an interface; the static pilot does not bind it to OmsOrderServiceImpl through Spring DI.",
            "status": "CHECK_REQUIRED",
        })

    result = {
        "schema_version": 1,
        "pilot_kind": "REAL_PUBLIC_BROWNFIELD_REPOSITORY",
        "repository": repository,
        "commit": commit,
        "source_root": str(source_root),
        "adapter_id": impact["adapter_id"],
        "adapter_completion_status": impact.get("completion_status"),
        "business_impact_confirmed": bool(impact.get("business_impact_confirmed", False)),
        "checks": checks,
        "check_failures": failures,
        "real_world_gaps": real_world_gaps,
        "adapter_coverage_gaps": impact.get("coverage_gaps", []),
        "summary": {
            "nodes": len(impact["nodes"]),
            "edges": len(impact["edges"]),
            "coverage_gaps": len(impact.get("coverage_gaps", [])),
            "required_checks_passed": len(checks) - len(failures),
            "required_checks_total": len(checks),
        },
        "reconciliation": {
            "execution_status": "NOT_RUN",
            "readiness": "WAITING_BUSINESS_AUTHORITY",
            "source_evidence_observed": True,
            "source_evidence_class": "CURRENT_SOURCE_DB_CONFIG_RUNTIME_EVIDENCE",
            "confirmed_human_business_truth_present": False,
            "reviewer_decision_present": False,
            "business_truth_auto_rewritten": False,
            "empirical_reconciliation_pass": False,
            "required_next_evidence": [
                "CONFIRMED_HUMAN_BUSINESS_TRUTH",
                "REVIEWER_DECISION"
            ],
            "interpretation": "공개 Repository는 실제 Source Evidence를 제공하지만 고객의 Confirmed Business Truth를 제공하지 않는다. 따라서 Impact integration PASS와 Brownfield Reconciliation empirical PASS는 분리한다."
        },
        "safety": {
            "production_complete_claimed": False,
            "business_truth_confirmed_from_source": False,
            "not_found_means_no_impact": False,
            "public_source_only_is_reconciliation_pass": False
        },
    }
    if failures:
        result["verdict"] = "FAIL_REQUIRED_RELATION_NOT_OBSERVED"
    elif impact.get("completion_status") == "COMPLETE":
        # A narrow static adapter should not suddenly claim real repository completeness.
        result["verdict"] = "FAIL_OVERCLAIMED_COMPLETE"
        result["check_failures"].append("adapter_must_remain_partial_on_current_scope")
    else:
        result["verdict"] = "PASS_REAL_REPOSITORY_PARTIAL_COVERAGE"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        result = validate(Path(args.source_root), args.repository, args.commit)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": result["verdict"],
        **result["summary"],
        "reconciliation_execution_status": result["reconciliation"]["execution_status"],
        "reconciliation_readiness": result["reconciliation"]["readiness"],
        "reconciliation_empirical_pass": result["reconciliation"]["empirical_reconciliation_pass"],
    }, ensure_ascii=False))
    return 0 if result["verdict"] == "PASS_REAL_REPOSITORY_PARTIAL_COVERAGE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
