#!/usr/bin/env python3
"""Build a deterministic verification result from a P0.4 test contract and execution result."""

from __future__ import annotations

import argparse
from pathlib import Path
import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def required_states(contract, execution):
    required = set((contract.get("execution_requirements") or {}).get("required_test_case_ids") or [])
    states = {c.get("id"): c.get("state") for c in ((execution.get("execution") or {}).get("cases") or [])}
    return required, states


def build(contract, execution):
    required, states = required_states(contract, execution)
    required_values = [states.get(tc) for tc in required]
    coverage_pass = (contract.get("coverage") or {}).get("coverage_percent") == 100
    actual_runtime = bool((execution.get("runtime_environment") or {}).get("actual_runtime"))
    blockers = list(execution.get("open_blockers") or [])
    business_reviewed = bool((contract.get("review") or {}).get("business_rule_candidate_reviewed"))
    production_source = bool((contract.get("source_binding") or {}).get("production_source"))
    all_passed = bool(required) and all(v == "PASSED" for v in required_values)
    any_failed = any(v == "FAILED" for v in required_values)
    any_executed = any(v in {"PASSED", "FAILED"} for v in required_values)

    if any_failed:
        state = "VERIFIED_FAIL"
    elif all_passed and actual_runtime and production_source and not blockers and business_reviewed:
        state = "VERIFIED_PASS"
    elif coverage_pass and not any_executed:
        state = "CONTRACT_PASS_RUNTIME_NOT_EXECUTED"
    elif any_executed:
        state = "PARTIAL_EVIDENCE"
    else:
        state = "NOT_VERIFIED"

    runtime_complete = bool(required) and all(v in {"PASSED", "FAILED"} for v in required_values)
    runtime_pass = state == "VERIFIED_PASS"
    production_verified = state == "VERIFIED_PASS" and production_source

    next_actions = []
    if not actual_runtime:
        next_actions.append("Provide actual runtime environment and execute all required tests")
    if not business_reviewed:
        next_actions.append("Resolve BUSINESS_RULE_REVIEW_OPEN with L2/Human")
    if not production_source:
        next_actions.append("Re-run against actual customer source before production verification")

    return {
        "schema_version": 1,
        "artifact_type": "VERIFICATION_RESULT",
        "verification_result_id": "VER-" + str(execution.get("execution_result_id") or "UNASSIGNED"),
        "subject": {
            "test_contract_id": contract.get("contract_id"),
            "test_execution_result_id": execution.get("execution_result_id"),
            "rq_group_candidate_id": (contract.get("subject") or {}).get("rq_group_candidate_id"),
        },
        "source_binding": {
            "source_evidence_set_id": (contract.get("source_binding") or {}).get("source_evidence_set_id"),
            "production_source": production_source,
        },
        "verification": {
            "state": state,
            "contract_coverage_pass": coverage_pass,
            "runtime_execution_complete": runtime_complete,
            "all_required_tests_passed": all_passed,
            "actual_runtime_environment": actual_runtime,
            "business_rule_candidate_reviewed": business_reviewed,
        },
        "claims": {
            "runtime_pass": runtime_pass,
            "production_verified": production_verified,
        },
        "stale_resolution": {
            "impact": "FIXTURE_CONTRACT_MATCH_ONLY",
            "pgm_spec": "FIXTURE_CONTRACT_MATCH_ONLY",
            "test_scenarios": "CONTRACT_COVERAGE_CURRENT_RUNTIME_UNVERIFIED",
            "requirement": "REVIEW_CANDIDATE",
        },
        "open_blockers": blockers,
        "required_next_actions": next_actions,
        "evidence": [
            "AC/TC direct mapping",
            "P0.3 source evidence set binding",
            "explicit runtime execution states",
        ],
        "status": state,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("contract", type=Path)
    p.add_argument("execution", type=Path)
    p.add_argument("-o", "--output", type=Path, required=True)
    a = p.parse_args()
    result = build(load(a.contract), load(a.execution))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: verification state={result['verification']['state']} output={a.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
