#!/usr/bin/env python3
"""Self-contained P0.7 reference adapter and conformance harness tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sdlc.adapters.reference import local_filesystem_source, subprocess_test
from run_provider_conformance import run_suite
from validate_p06_contracts import validate_response


def request(provider_type: str, operation: str, extensions=None):
    return {"provider_request": {
        "request_id": "P07-SELF",
        "provider_type": provider_type,
        "operation": operation,
        "project_context": {"project_id": "GENERIC", "mode": "BROWNFIELD", "stage": "TEST"},
        "target": {"target_type": "WORK_UNIT", "target_id": "GENERIC-1"},
        "write_intent": False,
        "extensions": extensions or {},
    }}


def response_root(response):
    return response["provider_response"]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        before = root / "before"; after = root / "after"; tests = root / "tests"
        before.mkdir(); after.mkdir(); tests.mkdir()
        (before / "module.txt").write_text("alpha\nneedle\n", encoding="utf-8")
        (after / "module.txt").write_text("alpha\nneedle changed\n", encoding="utf-8")
        (tests / "pass_case.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        (tests / "fail_case.py").write_text("raise SystemExit(4)\n", encoding="utf-8")
        (tests / "sleep_case.py").write_text("import time\ntime.sleep(1.0)\n", encoding="utf-8")

        src_cfg = {"root": str(before), "max_files": 100, "max_bytes": 100000, "max_output_chars": 10000}
        r = local_filesystem_source.invoke(request("SOURCE", "source.snapshot.read"), src_cfg)
        assert response_root(r)["status"] == "OK"
        assert response_root(r)["evidence"][0]["truth"] == "OBSERVED"

        r = local_filesystem_source.invoke(request("SOURCE", "source.search", {"query": "needle"}), src_cfg)
        assert len(response_root(r)["outputs"][0]["matches"]) == 1

        r = local_filesystem_source.invoke(request("SOURCE", "source.diff", {"before_root": str(before), "after_root": str(after)}), src_cfg)
        assert response_root(r)["status"] == "OK"
        assert "module.txt" in response_root(r)["outputs"][0]["changed_paths"]

        r = local_filesystem_source.invoke(request("SOURCE", "source.object.read", {"path": "../escape.txt"}), src_cfg)
        assert response_root(r)["open_items"][0]["code"] == "SOURCE_SCOPE_VIOLATION"

        r = local_filesystem_source.invoke(request("SOURCE", "source.snapshot.read"), {**src_cfg, "max_files": 0})
        assert response_root(r)["status"] == "PARTIAL"

        test_cfg = {"cwd": str(tests), "timeout_seconds": 1, "max_timeout_seconds": 2, "max_output_chars": 10000}
        r = subprocess_test.invoke(request("TEST", "test.discover", {"patterns": ["*_case.py"]}), test_cfg)
        assert len(response_root(r)["outputs"][0]["test_files"]) == 3

        r = subprocess_test.invoke(request("TEST", "test.discover"), test_cfg)
        assert response_root(r)["open_items"][0]["code"] == "TEST_DISCOVERY_PATTERN_REQUIRED"

        r = subprocess_test.invoke(request("TEST", "test.execute", {"command": [sys.executable, "pass_case.py"], "timeout_seconds": 0.5}), test_cfg)
        assert response_root(r)["status"] == "OK"
        assert response_root(r)["outputs"][0]["test_status"] == "PASSED"
        assert validate_response(r, request("TEST", "test.execute", {"command": [sys.executable, "pass_case.py"], "timeout_seconds": 0.5}), None) == []

        r = subprocess_test.invoke(request("TEST", "test.execute", {"command": [sys.executable, "fail_case.py"], "timeout_seconds": 0.5}), test_cfg)
        assert response_root(r)["status"] == "OK"
        assert response_root(r)["outputs"][0]["test_status"] == "FAILED"
        assert response_root(r)["outputs"][0]["exit_code"] == 4

        r = subprocess_test.invoke(request("TEST", "test.execute", {"command": [sys.executable, "sleep_case.py"], "timeout_seconds": 0.05}), test_cfg)
        assert response_root(r)["status"] == "BLOCKED"
        assert response_root(r)["open_items"][0]["code"] == "ADAPTER_TIMEOUT"
        assert response_root(r)["retryable"] is True

        r = subprocess_test.invoke(request("TEST", "test.execute", {"command": ["p07-command-does-not-exist"], "timeout_seconds": 0.5}), test_cfg)
        assert response_root(r)["open_items"][0]["code"] == "TEST_COMMAND_NOT_FOUND"

    source_suite = REPO_ROOT / "sdlc/design/validation/p0.7-provider-adapter-conformance-v1/source-adapter-suite.yaml"
    test_suite = REPO_ROOT / "sdlc/design/validation/p0.7-provider-adapter-conformance-v1/test-adapter-suite.yaml"
    source_result, source_errors = run_suite(source_suite)
    test_result, test_errors = run_suite(test_suite)
    assert source_errors == [], source_errors
    assert test_errors == [], test_errors
    assert source_result["summary"]["status"] == "PASS"
    assert test_result["summary"]["status"] == "PASS"

    core_paths = [
        REPO_ROOT / "sdlc/design/contracts/provider-adapter-conformance.md",
        REPO_ROOT / "sdlc/adapters/reference/local_filesystem_source.py",
        REPO_ROOT / "sdlc/adapters/reference/subprocess_test.py",
        REPO_ROOT / "sdlc/scripts/run_provider_conformance.py",
    ]
    forbidden = ["REQ_TM_TE", "RQG-CAND-6BB6D66548", "근태", "AttendanceClose", "TB_ATT_", "10분"]
    for path in core_paths:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (path, token)

    print("OK: P0.7 provider adapter conformance tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
