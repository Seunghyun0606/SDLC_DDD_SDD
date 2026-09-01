#!/usr/bin/env python3
"""Deterministic P0.4 validators for TEST -> VERIFY."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
import yaml

HASH64 = re.compile(r"^[0-9a-f]{64}$")
TEST_STATES = {"NOT_EXECUTED", "PASSED", "FAILED", "BLOCKED", "SKIPPED_WITH_REASON"}
VERIFY_STATES = {"NOT_VERIFIED", "CONTRACT_PASS_RUNTIME_NOT_EXECUTED", "PARTIAL_EVIDENCE", "VERIFIED_PASS", "VERIFIED_FAIL"}


def add(errors, code, msg):
    errors.append(f"{code}: {msg}")


def ids(items):
    return [x.get("id") for x in items if isinstance(x, dict)]


def validate_contract(c):
    errors = []
    if c.get("artifact_type") != "TEST_CONTRACT" or not c.get("contract_id"):
        add(errors, "TV-001", "TEST_CONTRACT and contract_id are required")
    subject = c.get("subject") or {}
    if not subject.get("rq_group_candidate_id"):
        add(errors, "TV-001", "subject.rq_group_candidate_id is required")
    binding = c.get("source_binding") or {}
    if not HASH64.match(str(binding.get("source_evidence_set_id", ""))):
        add(errors, "TV-001", "source_evidence_set_id must be sha256")
    ac = c.get("acceptance_criteria") or []
    tc = c.get("test_cases") or []
    ac_ids, tc_ids = ids(ac), ids(tc)
    if not ac_ids or not tc_ids:
        add(errors, "TV-001", "acceptance_criteria and test_cases are required")
    if len(tc_ids) != len(set(tc_ids)):
        add(errors, "TV-002", "duplicate test case id")
    if len(ac_ids) != len(set(ac_ids)):
        add(errors, "TV-001", "duplicate acceptance criterion id")
    known = set(ac_ids)
    covered = set()
    for i, case in enumerate(tc):
        refs = set(case.get("ac_ids") or [])
        unknown = refs - known
        if unknown:
            add(errors, "TV-004", f"test_cases[{i}] references unknown AC: {sorted(unknown)}")
        covered |= refs
    required_ac = set((c.get("coverage") or {}).get("required_ac_ids") or ac_ids)
    uncovered = required_ac - covered
    if uncovered:
        add(errors, "TV-003", f"required AC not covered: {sorted(uncovered)}")
    declared_uncovered = set((c.get("coverage") or {}).get("uncovered_ac_ids") or [])
    pct = (c.get("coverage") or {}).get("coverage_percent")
    calc = 0 if not required_ac else round(100 * len(required_ac & covered) / len(required_ac))
    if declared_uncovered != uncovered or pct != calc:
        add(errors, "TV-003", f"coverage declaration mismatch: expected {calc}% and {sorted(uncovered)}")
    required_tc = set((c.get("execution_requirements") or {}).get("required_test_case_ids") or [])
    if not required_tc or not required_tc.issubset(set(tc_ids)):
        add(errors, "TV-001", "required_test_case_ids must reference known tests")
    return errors


def validate_execution(c, e):
    errors = validate_contract(c)
    if e.get("artifact_type") != "TEST_EXECUTION_RESULT" or not e.get("execution_result_id"):
        add(errors, "TV-001", "TEST_EXECUTION_RESULT and execution_result_id are required")
    if (e.get("subject") or {}).get("test_contract_id") != c.get("contract_id"):
        add(errors, "TV-001", "execution test_contract_id mismatch")
    if (e.get("source_binding") or {}).get("source_evidence_set_id") != (c.get("source_binding") or {}).get("source_evidence_set_id"):
        add(errors, "TV-008", "source evidence set mismatch")
    required = set((c.get("execution_requirements") or {}).get("required_test_case_ids") or [])
    cases = ((e.get("execution") or {}).get("cases") or [])
    case_ids = ids(cases)
    if len(case_ids) != len(set(case_ids)):
        add(errors, "TV-002", "duplicate execution test case id")
    if not required.issubset(set(case_ids)):
        add(errors, "TV-001", "all required tests need explicit execution state")
    counts = {"PASSED": 0, "FAILED": 0, "BLOCKED": 0, "NOT_EXECUTED": 0, "SKIPPED_WITH_REASON": 0}
    for i, case in enumerate(cases):
        state = case.get("state")
        if state not in TEST_STATES:
            add(errors, "TV-001", f"execution.cases[{i}] invalid state")
            continue
        counts[state] += 1
        evidence = case.get("evidence") or []
        actual = case.get("actual_result")
        reason = case.get("reason")
        if state in {"PASSED", "FAILED"} and (not evidence or actual in (None, "")):
            add(errors, "TV-005", f"{case.get('id')} {state} requires actual_result and evidence")
        if state == "NOT_EXECUTED" and (actual not in (None, "") or evidence):
            add(errors, "TV-006", f"{case.get('id')} NOT_EXECUTED must not contain runtime result/evidence")
        if state in {"BLOCKED", "SKIPPED_WITH_REASON"} and not reason:
            add(errors, "TV-007", f"{case.get('id')} {state} requires reason")
    s = e.get("summary") or {}
    expected = {
        "required": len(required), "passed": counts["PASSED"], "failed": counts["FAILED"],
        "blocked": counts["BLOCKED"], "not_executed": counts["NOT_EXECUTED"], "skipped": counts["SKIPPED_WITH_REASON"],
    }
    for key, value in expected.items():
        if s.get(key) != value:
            add(errors, "TV-001", f"summary.{key} expected {value}, got {s.get(key)}")
    return errors


def validate_verification(c, e, v):
    errors = validate_execution(c, e)
    if v.get("artifact_type") != "VERIFICATION_RESULT":
        add(errors, "TV-001", "VERIFICATION_RESULT is required")
        return errors
    ver = v.get("verification") or {}
    state = ver.get("state")
    if state not in VERIFY_STATES:
        add(errors, "TV-001", "invalid verification state")
        return errors
    if (v.get("source_binding") or {}).get("source_evidence_set_id") != (c.get("source_binding") or {}).get("source_evidence_set_id"):
        add(errors, "TV-008", "verification source evidence set mismatch")
    required = set((c.get("execution_requirements") or {}).get("required_test_case_ids") or [])
    states = {x.get("id"): x.get("state") for x in ((e.get("execution") or {}).get("cases") or [])}
    all_passed = bool(required) and all(states.get(tc) == "PASSED" for tc in required)
    actual_runtime = bool((e.get("runtime_environment") or {}).get("actual_runtime"))
    blockers = list(e.get("open_blockers") or [])
    reviewed = bool((c.get("review") or {}).get("business_rule_candidate_reviewed"))
    production_source = bool((c.get("source_binding") or {}).get("production_source"))
    claims = v.get("claims") or {}
    if state == "VERIFIED_PASS":
        if not all_passed:
            add(errors, "TV-009", "VERIFIED_PASS requires all required tests PASSED")
        if not actual_runtime:
            add(errors, "TV-010", "VERIFIED_PASS requires actual runtime environment")
        if blockers:
            add(errors, "TV-011", "VERIFIED_PASS cannot have open blockers")
        if not reviewed:
            add(errors, "TV-012", "VERIFIED_PASS requires business rule review")
        if not production_source:
            add(errors, "TV-013", "synthetic fixture cannot be production VERIFIED_PASS")
    if claims.get("runtime_pass") and not (all_passed and actual_runtime):
        add(errors, "TV-009", "runtime_pass claim requires all passed in actual runtime")
    if claims.get("production_verified") and not (state == "VERIFIED_PASS" and production_source):
        add(errors, "TV-013", "production verification claim is not allowed")
    if state == "CONTRACT_PASS_RUNTIME_NOT_EXECUTED":
        if (c.get("coverage") or {}).get("coverage_percent") != 100:
            add(errors, "TV-003", "contract pass requires 100% AC coverage")
        if claims.get("runtime_pass") or claims.get("production_verified"):
            add(errors, "TV-009", "contract-only state cannot claim runtime/production pass")
    return errors


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["test-contract", "test-execution", "verification"])
    p.add_argument("paths", nargs="+")
    a = p.parse_args()
    try:
        if a.kind == "test-contract" and len(a.paths) == 1:
            errors = validate_contract(load(a.paths[0]))
        elif a.kind == "test-execution" and len(a.paths) == 2:
            errors = validate_execution(load(a.paths[0]), load(a.paths[1]))
        elif a.kind == "verification" and len(a.paths) == 3:
            errors = validate_verification(load(a.paths[0]), load(a.paths[1]), load(a.paths[2]))
        else:
            print("TV-001: invalid path count", file=sys.stderr); return 2
    except Exception as exc:
        print(f"TV-001: load error: {exc}", file=sys.stderr); return 2
    if errors:
        print("\n".join(errors), file=sys.stderr); return 1
    print(f"OK: P0.4 {a.kind} contract valid")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
