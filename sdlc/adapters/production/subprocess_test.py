#!/usr/bin/env python3
"""Allowlisted subprocess TEST adapter with actual execution evidence.

Provider status reports whether execution machinery worked; test_status reports whether tests passed.
An exit code != 0 is therefore an observed FAILED test, not a provider failure.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ADAPTER_VERSION = "P0-PROD-1"
PROVIDER_ID = "allowlisted-subprocess-test"
PROVIDER_TYPE = "TEST"
CAPABILITIES = ["test.discover", "test.execute", "test.result.read"]


def describe() -> dict[str, Any]:
    return {"provider_id": PROVIDER_ID, "provider_type": PROVIDER_TYPE, "provider_state": "AVAILABLE", "mode": "READ_WRITE",
            "capabilities": list(CAPABILITIES), "adapter_version": ADAPTER_VERSION, "production_candidate": True}


def _response(req, status, revision, outputs, evidence, open_items, warnings, retryable=False, extensions=None):
    return {"schema_version": 1, "provider_response": {"request_id": req.get("request_id"), "provider_id": PROVIDER_ID,
            "provider_type": PROVIDER_TYPE, "operation": req.get("operation"), "status": status,
            "provider_revision": revision or "UNAVAILABLE", "outputs": outputs, "evidence": evidence,
            "open_items": open_items, "warnings": warnings, "retryable": retryable, "extensions": extensions or {}}}


def _blocked(req, code, message, revision="UNAVAILABLE", retryable=False):
    return _response(req, "BLOCKED", revision, [], [], [{"code": code, "message": message}], [], retryable)


def _cwd(req, config) -> Path | None:
    raw = (req.get("extensions") or {}).get("cwd") or config.get("cwd")
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    return path if path.is_dir() else None


def _fingerprint(command: list[str], cwd: Path) -> str:
    return hashlib.sha256((json.dumps(command, ensure_ascii=False) + "\0" + str(cwd)).encode("utf-8")).hexdigest()


def _allowed(command: list[str], allowlist: list[list[str]]) -> bool:
    for allowed in allowlist:
        if command == allowed:
            return True
    return False


def invoke(request_doc: dict[str, Any], adapter_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = adapter_config or {}
    req = (request_doc or {}).get("provider_request") or request_doc
    operation = req.get("operation")
    if operation not in CAPABILITIES:
        return _blocked(req, "UNSUPPORTED_OPERATION", f"unsupported capability: {operation}")
    cwd = _cwd(req, config)
    if cwd is None:
        return _blocked(req, "TEST_CWD_UNAVAILABLE", "configured test cwd is missing")
    ext = req.get("extensions") or {}
    max_output = int(config.get("max_output_chars", 50_000))

    if operation == "test.discover":
        allowlist = config.get("allowed_commands") or []
        outputs = [{"allowed_commands": allowlist, "actual_runtime": True}]
        revision = hashlib.sha256(json.dumps(allowlist, sort_keys=True).encode("utf-8")).hexdigest()
        evidence = [{"evidence_id": "EV-TEST-DISCOVER-PROD-001", "truth": "OBSERVED", "locator": str(cwd), "revision": revision,
                     "observed_value": {"allowed_command_count": len(allowlist)}}]
        return _response(req, "OK", revision, outputs, evidence, [], [])

    if operation == "test.result.read":
        relative = str(ext.get("result_path") or "")
        if not relative:
            return _blocked(req, "TEST_RESULT_PATH_REQUIRED", "extensions.result_path is required")
        try:
            path = (cwd / relative).resolve(); path.relative_to(cwd)
        except (ValueError, OSError):
            return _blocked(req, "TEST_SCOPE_VIOLATION", "result path escapes test cwd")
        if not path.is_file():
            return _blocked(req, "TEST_RESULT_NOT_FOUND", relative)
        raw = path.read_bytes(); digest = hashlib.sha256(raw).hexdigest()
        content = raw.decode("utf-8", errors="replace")[:max_output]
        evidence = [{"evidence_id": "EV-TEST-RESULT-PROD-001", "truth": "OBSERVED", "locator": relative, "revision": digest,
                     "observed_value": {"sha256": digest, "content": content}}]
        return _response(req, "OK", digest, [{"result_path": relative, "sha256": digest, "content": content}], evidence, [], [])

    command = ext.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        return _blocked(req, "TEST_COMMAND_INVALID", "extensions.command must be a non-empty argv list")
    allowlist = config.get("allowed_commands") or []
    if not all(isinstance(x, list) for x in allowlist) or not _allowed(command, allowlist):
        return _blocked(req, "TEST_COMMAND_NOT_ALLOWLISTED", "requested argv must exactly match adapter_config.allowed_commands")
    timeout = float(ext.get("timeout_seconds", config.get("timeout_seconds", 120)))
    max_timeout = float(config.get("max_timeout_seconds", 900))
    if timeout <= 0 or timeout > max_timeout:
        return _blocked(req, "TEST_TIMEOUT_INVALID", f"timeout must be >0 and <= {max_timeout}")
    revision = _fingerprint(command, cwd)
    try:
        cp = subprocess.run(command, cwd=str(cwd), shell=False, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        return _response(req, "BLOCKED", revision, [], [], [{"code": "TEST_TIMEOUT", "message": f"exceeded {timeout}s"}],
                         [str(exc.stdout or "")[:max_output], str(exc.stderr or "")[:max_output]], retryable=False)
    except FileNotFoundError as exc:
        return _blocked(req, "TEST_COMMAND_NOT_FOUND", str(exc), revision)
    except OSError as exc:
        return _response(req, "ERROR", revision, [], [], [{"code": "TEST_PROCESS_ERROR", "message": str(exc)}], [], retryable=True)

    stdout = (cp.stdout or "")[:max_output]; stderr = (cp.stderr or "")[:max_output]
    test_status = "PASSED" if cp.returncode == 0 else "FAILED"
    output_hash = hashlib.sha256((stdout + "\0" + stderr).encode("utf-8")).hexdigest()
    evidence = [{"evidence_id": "EV-TEST-EXEC-PROD-001", "truth": "OBSERVED", "locator": "subprocess:" + " ".join(command), "revision": revision,
                 "observed_value": {"exit_code": cp.returncode, "test_status": test_status, "output_sha256": output_hash, "actual_runtime": True}}]
    outputs = [{"test_status": test_status, "exit_code": cp.returncode, "stdout": stdout, "stderr": stderr,
                "command": command, "actual_runtime": True, "execution_evidence": True}]
    return _response(req, "OK", revision, outputs, evidence, [], [], extensions={"actual_runtime": True, "test_pass_claim_allowed": test_status == "PASSED"})
