#!/usr/bin/env python3
"""Validate a low-level Agent stage result against its real artifact and Canonical delta.

This does not call an LLM and does not claim to prove language-model determinism.
It makes repeated runs measurable by validating one small result envelope and
computing a semantic fingerprint that ignores explicitly volatile timestamps.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
APPLY_PATH = SCRIPT_DIR / "apply_canonical_delta.py"
SPEC = importlib.util.spec_from_file_location("apply_canonical_delta_for_stage_result", APPLY_PATH)
APPLY = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(APPLY)

STAGES = {
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION", "CHANGE",
}
QUALITY = {"PASS", "WARNING", "FAIL"}
UNCERTAINTY = {"OPEN", "CHECK_REQUIRED", "CONFLICT", "STALE"}
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
VOLATILE_ARTIFACT_LINE_RE = re.compile(r"^\s*(?:generated_at|updated_at|created_at):\s*.*$", re.I)
VOLATILE_RESULT_KEYS = {"generated_at", "updated_at", "created_at", "checked_at", "observed_at"}


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _error(code: str, message: str, **extra) -> dict:
    return {"code": code, "message": message, **extra}


def _safe_artifact_path(root: Path, raw: str) -> tuple[Path | None, dict | None]:
    path = Path(raw)
    if path.is_absolute():
        return None, _error("ABSOLUTE_ARTIFACT_PATH", "artifact_path must be repository-relative")
    root_resolved = root.resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError:
        return None, _error("ARTIFACT_PATH_TRAVERSAL", "artifact_path escapes root", artifact_path=raw)
    return resolved, None


def _normalize_artifact(text: str) -> str:
    lines = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if VOLATILE_ARTIFACT_LINE_RE.match(raw):
            continue
        lines.append(raw.rstrip())
    return "\n".join(lines).strip() + "\n"


def _strip_volatile(value):
    if isinstance(value, dict):
        return {
            key: _strip_volatile(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_RESULT_KEYS
        }
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value


def semantic_payload(result: dict, artifact_text: str) -> dict:
    quality = result.get("quality_gate") or {}
    return {
        "stage": result.get("stage"),
        "artifact": _normalize_artifact(artifact_text),
        "canonical_delta": _strip_volatile(result.get("canonical_delta") or {}),
        "quality_gate": _strip_volatile(quality),
        "alerts": _strip_volatile(result.get("alerts") or []),
        "uncertainty": _strip_volatile(result.get("uncertainty") or []),
    }


def semantic_fingerprint(result: dict, artifact_text: str) -> str:
    payload = json.dumps(semantic_payload(result, artifact_text), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_stage_result(result: dict, root: Path, *, store_path: Path | None = None) -> dict:
    errors = []
    warnings = []

    if result.get("schema_version") != 1:
        errors.append(_error("INVALID_SCHEMA_VERSION", "stage result schema_version must be 1"))

    stage = str(result.get("stage") or "").strip()
    if stage not in STAGES:
        errors.append(_error("INVALID_STAGE", "unknown or missing stage", stage=stage))

    artifact_raw = str(result.get("artifact_path") or "").strip()
    artifact_path = None
    artifact_text = ""
    if not artifact_raw:
        errors.append(_error("MISSING_ARTIFACT_PATH", "artifact_path is required"))
    else:
        artifact_path, path_error = _safe_artifact_path(root, artifact_raw)
        if path_error:
            errors.append(path_error)
        elif not artifact_path.is_file():
            errors.append(_error("ARTIFACT_NOT_FOUND", "artifact_path does not exist", artifact_path=artifact_raw))
        else:
            artifact_text = artifact_path.read_text(encoding="utf-8")
            if not artifact_text.strip():
                errors.append(_error("EMPTY_ARTIFACT", "artifact is empty", artifact_path=artifact_raw))
            placeholders = sorted(set(PLACEHOLDER_RE.findall(artifact_text)))
            if placeholders:
                errors.append(_error(
                    "UNRESOLVED_TEMPLATE_PLACEHOLDER",
                    "artifact contains unresolved template placeholders",
                    placeholders=placeholders[:20],
                ))

    delta = result.get("canonical_delta")
    if not isinstance(delta, dict):
        errors.append(_error("MISSING_CANONICAL_DELTA", "canonical_delta object is required"))
    else:
        for item in APPLY.validate_delta(delta):
            errors.append(_error("CANONICAL_DELTA_INVALID", item.get("message", "invalid canonical delta"), detail=item))
        if stage and delta.get("stage") != stage:
            errors.append(_error(
                "STAGE_DELTA_MISMATCH",
                "canonical_delta.stage must match stage result",
                stage=stage,
                delta_stage=delta.get("stage"),
            ))
        if artifact_raw and delta.get("source_artifact") != artifact_raw:
            errors.append(_error(
                "ARTIFACT_DELTA_SOURCE_MISMATCH",
                "canonical_delta.source_artifact must equal artifact_path",
                artifact_path=artifact_raw,
                source_artifact=delta.get("source_artifact"),
            ))

    quality_gate = result.get("quality_gate")
    if not isinstance(quality_gate, dict) or quality_gate.get("status") not in QUALITY:
        errors.append(_error("INVALID_QUALITY_GATE", "quality_gate.status must be PASS, WARNING, or FAIL"))
    elif quality_gate.get("status") == "FAIL":
        warnings.append(_error("QUALITY_GATE_FAILED", "stage result is structurally valid but not executable"))

    alerts = result.get("alerts", [])
    if not isinstance(alerts, list):
        errors.append(_error("INVALID_ALERTS", "alerts must be an array"))

    uncertainty = result.get("uncertainty", [])
    if not isinstance(uncertainty, list):
        errors.append(_error("INVALID_UNCERTAINTY", "uncertainty must be an array"))
    else:
        for index, item in enumerate(uncertainty):
            state = item.get("state") if isinstance(item, dict) else item
            if state not in UNCERTAINTY:
                errors.append(_error(
                    "INVALID_UNCERTAINTY_STATE",
                    "uncertainty state is invalid",
                    index=index,
                    state=state,
                ))

    canonical_check = None
    if not errors and store_path is not None and isinstance(delta, dict):
        store = APPLY.load_store(store_path)
        apply_result, _ = APPLY.apply_delta(store, delta)
        canonical_check = apply_result
        if apply_result["status"] not in {"APPLIED", "IDEMPOTENT", "NO_CHANGE"}:
            errors.append(_error(
                "CANONICAL_APPLY_NOT_EXECUTABLE",
                "canonical delta cannot be applied to the current store",
                apply_result=apply_result,
            ))

    fingerprint = semantic_fingerprint(result, artifact_text) if artifact_text and not errors else None
    executable = not errors and isinstance(quality_gate, dict) and quality_gate.get("status") != "FAIL"
    return {
        "status": "PASS" if not errors else "FAIL",
        "executable": executable,
        "stage": stage or None,
        "artifact_path": artifact_raw or None,
        "semantic_fingerprint": fingerprint,
        "canonical_check": canonical_check,
        "errors": errors,
        "warnings": warnings,
    }


def compare_stage_results(first: dict, first_artifact: str, second: dict, second_artifact: str) -> dict:
    first_fp = semantic_fingerprint(first, first_artifact)
    second_fp = semantic_fingerprint(second, second_artifact)
    return {
        "status": "MATCH" if first_fp == second_fp else "MISMATCH",
        "first_fingerprint": first_fp,
        "second_fingerprint": second_fp,
    }


def _artifact_text_for_result(result: dict, root: Path) -> str:
    raw = str(result.get("artifact_path") or "")
    path, error = _safe_artifact_path(root, raw)
    if error or path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate low-level Agent stage output and optionally compare repeated runs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--result", required=True)
    parser.add_argument("--store")
    parser.add_argument("--compare")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    root = Path(args.root)
    result_path = Path(args.result)
    result = load_json(result_path)
    validation = validate_stage_result(result, root, store_path=Path(args.store) if args.store else None)
    output = {"validation": validation}

    exit_code = 0 if validation["status"] == "PASS" else 2
    if args.compare:
        other = load_json(Path(args.compare))
        first_artifact = _artifact_text_for_result(result, root)
        second_artifact = _artifact_text_for_result(other, root)
        comparison = compare_stage_results(result, first_artifact, other, second_artifact)
        output["comparison"] = comparison
        if comparison["status"] != "MATCH":
            exit_code = 4

    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
