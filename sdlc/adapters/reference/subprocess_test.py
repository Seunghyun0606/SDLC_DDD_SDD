#!/usr/bin/env python3
"""Stack-neutral subprocess TEST reference adapter for P0.7."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

ADAPTER_VERSION = "P0.7-1"
PROVIDER_ID = "reference-subprocess-test"
PROVIDER_TYPE = "TEST"
CAPABILITIES = ["test.discover", "test.execute", "test.result.read"]


def describe() -> dict[str, Any]:
    return {
        "provider_id": PROVIDER_ID,
        "provider_type": PROVIDER_TYPE,
        "provider_state": "AVAILABLE",
        "mode": "READ_WRITE",
        "capabilities": list(CAPABILITIES),
        "adapter_version": ADAPTER_VERSION,
    }


def _response(req: dict[str, Any], status: str, revision: str, outputs: list[Any], evidence: list[dict[str, Any]],
              open_items: list[dict[str, Any]], warnings: list[str], retryable: bool = False,
              extensions: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "provider_response": {
            "request_id": req.get("request_id"),
            "provider_id": PROVIDER_ID,
            "provider_type": PROVIDER_TYPE,
            "operation": req.get("operation"),
            "status": status,
            "provider_revision": revision,
            "outputs": outputs,
            "evidence": evidence,
            "open_items": open_items,
            "warnings": warnings,
            "retryable": retryable,
            "extensions": extensions or {},
        },
    }


def _blocked(req: dict[str, Any], code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return _response(req, "BLOCKED", "UNAVAILABLE", [], [], [{"code": code, "message": message}], [], retryable)


def _revision(command: list[str], cwd: str) -> str:
    raw = "\0".join(command) + "\0" + cwd
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cwd(req: dict[str, Any], config: dict[str, Any]) -> Path | None:
    raw = (req.get("extensions") or {}).get("cwd") or config.get("cwd")
    if not raw:
        return None
    path = Path(raw).expanduser().resolve()
    return path if path.exists() and path.is_dir() else None


def invoke(request_doc: dict[str, Any], adapter_config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = adapter_config or {}
    req = (request_doc or {}).get("provider_request") or request_doc
    operation = req.get("operation")
    if operation not in CAPABILITIES:
        return _blocked(req, "UNSUPPORTED_OPERATION", f"unsupported capability: {operation}")
    cwd = _cwd(req, config)
    if cwd is None:
        return _blocked(req, "TEST_CWD_UNAVAILABLE", "configured test working directory is missing")

    ext = req.get("extensions") or {}
    max_output_chars = int(config.get("max_output_chars", 20_000))

    if operation == "test.discover":
        patterns = ext.get("patterns") or config.get("patterns")
        if not isinstance(patterns, list) or not patterns:
            return _blocked(req, "TEST_DISCOVERY_PATTERN_REQUIRED", "test discovery patterns must be injected by project/adapter configuration")
        found: set[str] = set()
        for pattern in patterns:
            for path in cwd.rglob(str(pattern)):
                if path.is_file():
                    found.add(path.relative_to(cwd).as_posix())
        revision = hashlib.sha256("\n".join(sorted(found)).encode("utf-8")).hexdigest()
        evidence = [{"evidence_id": "EV-TEST-DISCOVER-001", "truth": "OBSERVED", "locator": str(cwd),
                     "revision": revision, "observed_value": {"test_file_count": len(found)}}]
        return _response(req, "OK", revision, [{"test_files": sorted(found)}], evidence, [], [])

    if operation == "test.result.read":
        relative = str(ext.get("result_path") or "")
        if not relative:
            return _blocked(req, "TEST_RESULT_PATH_REQUIRED", "extensions.result_path is required")
        try:
            path = (cwd / relative).resolve(); path.relative_to(cwd)
        except (ValueError, OSError):
            return _blocked(req, "TEST_SCOPE_VIOLATION", "result path is outside configured cwd")
        if not path.is_file():
            return _blocked(req, "TEST_RESULT_NOT_FOUND", f"test result not found: {relative}")
        data = path.read_text(encoding="utf-8", errors="replace")[:max_output_chars]
        revision = hashlib.sha256(path.read_bytes()).hexdigest()
        evidence = [{"evidence_id": "EV-TEST-RESULT-001", "truth": "OBSERVED", "locator": relative,
                     "revision": revision, "observed_value": {"content": data}}]
        return _response(req, "OK", revision, [{"result_path": relative, "content": data}], evidence, [], [])

    command = ext.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        return _blocked(req, "TEST_COMMAND_INVALID", "extensions.command must be a non-empty argv string list")
    timeout_seconds = float(ext.get("timeout_seconds", config.get("timeout_seconds", 30)))
    max_timeout = float(config.get("max_timeout_seconds", 120))
    if timeout_seconds <= 0 or timeout_seconds > max_timeout:
        return _blocked(req, "TEST_TIMEOUT_INVALID", f"timeout must be >0 and <= {max_timeout}")
    revision = _revision(command, str(cwd))
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _response(
            req, "BLOCKED", revision, [], [],
            [{"code": "ADAPTER_TIMEOUT", "message": f"test command exceeded {timeout_seconds}s"}],
            [f"stdout before timeout: {(exc.stdout or '')[:max_output_chars]}", f"stderr before timeout: {(exc.stderr or '')[:max_output_chars]}"],
            retryable=True,
        )
    except FileNotFoundError as exc:
        return _blocked(req, "TEST_COMMAND_NOT_FOUND", str(exc), retryable=False)
    except OSError as exc:
        return _response(req, "ERROR", revision, [], [], [{"code": "TEST_PROCESS_ERROR", "message": str(exc)}], [], retryable=True)

    stdout = (completed.stdout or "")[:max_output_chars]
    stderr = (completed.stderr or "")[:max_output_chars]
    test_status = "PASSED" if completed.returncode == 0 else "FAILED"
    evidence = [{
        "evidence_id": "EV-TEST-EXECUTE-001",
        "truth": "OBSERVED",
        "locator": "subprocess:" + " ".join(command),
        "revision": revision,
        "observed_value": {"exit_code": completed.returncode, "test_status": test_status},
    }]
    outputs = [{
        "test_status": test_status,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "command": command,
    }]
    return _response(req, "OK", revision, outputs, evidence, [], [])
