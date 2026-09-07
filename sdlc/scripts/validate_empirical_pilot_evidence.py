#!/usr/bin/env python3
"""Validate observed SDLC Harness pilot evidence without converting declarations into empirical PASS."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PILOT_TYPES = {
    "EXTERNAL_AGENT_TAILORING_SEMANTIC_EQUIVALENCE",
    "HUMAN_FIRST_USE",
    "BROWNFIELD_RECONCILIATION",
}
REQUIRED_PROFILES = ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL"]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("pilot evidence must be a JSON object")
    return data


def _claim_is_true(data: dict[str, Any]) -> bool:
    claims = data.get("claims") or {}
    return isinstance(claims, dict) and any(value is True for value in claims.values())


def _required_text(data: dict[str, Any], key: str, errors: list[str]) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        errors.append(f"MISSING_{key.upper()}")
    return value


def _validate_external_agent(data: dict[str, Any], errors: list[str]) -> bool:
    provider = data.get("provider") or {}
    if not isinstance(provider, dict):
        errors.append("INVALID_PROVIDER")
        provider = {}
    if str(provider.get("declared_class") or "") != "EXTERNAL_AGENT":
        errors.append("PROVIDER_CLASS_NOT_EXTERNAL_AGENT")
    if not str(provider.get("provider_id") or "").strip():
        errors.append("MISSING_PROVIDER_ID")
    identity = provider.get("identity_evidence") or []
    if not isinstance(identity, list) or not identity or not all(str(x).strip() for x in identity):
        errors.append("MISSING_PROVIDER_IDENTITY_EVIDENCE")

    canonical = data.get("canonical") or {}
    fingerprint = str(canonical.get("fingerprint") or "") if isinstance(canonical, dict) else ""
    if not fingerprint.startswith("sha256:"):
        errors.append("MISSING_CANONICAL_FINGERPRINT")

    runs = data.get("profile_runs") or []
    if not isinstance(runs, list):
        errors.append("INVALID_PROFILE_RUNS")
        runs = []
    by_profile = {str(row.get("profile_id") or ""): row for row in runs if isinstance(row, dict)}
    if any(profile not in by_profile for profile in REQUIRED_PROFILES):
        errors.append("MISSING_REQUIRED_PROFILE_RUN")

    semantic_pass = True
    for profile in REQUIRED_PROFILES:
        row = by_profile.get(profile)
        if not isinstance(row, dict):
            semantic_pass = False
            continue
        paths = row.get("artifact_paths") or []
        if not isinstance(paths, list) or not paths or not all(str(x).strip() for x in paths):
            errors.append(f"MISSING_ARTIFACT_PATHS_{profile}")
            semantic_pass = False
        review = row.get("semantic_review") or {}
        if not isinstance(review, dict) or not str(review.get("reviewer") or "").strip():
            errors.append(f"MISSING_SEMANTIC_REVIEW_{profile}")
            semantic_pass = False
            continue
        if review.get("meaning_preserved") is not True:
            semantic_pass = False
        unsupported = review.get("unsupported_business_fact_count")
        omission = review.get("material_omission_count")
        if not isinstance(unsupported, int) or unsupported < 0:
            errors.append(f"INVALID_UNSUPPORTED_FACT_COUNT_{profile}")
            semantic_pass = False
        elif unsupported != 0:
            semantic_pass = False
        if not isinstance(omission, int) or omission < 0:
            errors.append(f"INVALID_OMISSION_COUNT_{profile}")
            semantic_pass = False
        elif omission != 0:
            semantic_pass = False
    return semantic_pass


def _validate_human_first_use(data: dict[str, Any], errors: list[str]) -> bool:
    participants = data.get("participants") or []
    if not isinstance(participants, list):
        errors.append("INVALID_PARTICIPANTS")
        participants = []
    if len(participants) < 3:
        errors.append("INSUFFICIENT_PARTICIPANT_COUNT")

    pass_state = len(participants) >= 3
    seen: set[str] = set()
    for index, row in enumerate(participants, 1):
        if not isinstance(row, dict):
            errors.append(f"INVALID_PARTICIPANT_{index}")
            pass_state = False
            continue
        participant_id = str(row.get("participant_id") or "").strip()
        if not participant_id or participant_id in seen:
            errors.append(f"INVALID_PARTICIPANT_ID_{index}")
            pass_state = False
        seen.add(participant_id)
        if not str(row.get("role") or "").strip():
            errors.append(f"MISSING_PARTICIPANT_ROLE_{index}")
            pass_state = False
        if row.get("started_from_start_here") is not True:
            pass_state = False
        if row.get("completed_without_framework_designer") is not True:
            pass_state = False
        blockers = row.get("critical_blocker_count")
        if not isinstance(blockers, int) or blockers < 0:
            errors.append(f"INVALID_BLOCKER_COUNT_{index}")
            pass_state = False
        elif blockers != 0:
            pass_state = False
        rating = row.get("review_burden_rating_1_to_5")
        if not isinstance(rating, int) or not 1 <= rating <= 5:
            errors.append(f"INVALID_REVIEW_BURDEN_RATING_{index}")
            pass_state = False
    return pass_state


def _validate_brownfield(data: dict[str, Any], errors: list[str]) -> bool:
    evidence = data.get("evidence") or []
    if not isinstance(evidence, list):
        errors.append("INVALID_EVIDENCE")
        evidence = []
    classes = {
        str(row.get("evidence_class") or "")
        for row in evidence
        if isinstance(row, dict)
    }
    required = {
        "CURRENT_SOURCE_DB_CONFIG_RUNTIME_EVIDENCE",
        "CONFIRMED_HUMAN_BUSINESS_TRUTH",
    }
    if not required.issubset(classes):
        errors.append("MISSING_BROWNFIELD_AUTHORITY_EVIDENCE")
    if not str(data.get("reviewer_decision") or "").strip():
        errors.append("MISSING_REVIEWER_DECISION")
    auto_rewritten = data.get("business_truth_auto_rewritten")
    if auto_rewritten is not False:
        errors.append("BUSINESS_TRUTH_AUTO_REWRITE_NOT_FALSE")
    return required.issubset(classes) and bool(str(data.get("reviewer_decision") or "").strip()) and auto_rewritten is False


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("UNSUPPORTED_SCHEMA_VERSION")
    pilot_type = str(data.get("pilot_type") or "")
    if pilot_type not in PILOT_TYPES:
        errors.append("UNSUPPORTED_PILOT_TYPE")
    status = str(data.get("execution_status") or "")
    if status not in {"NOT_RUN", "OBSERVED"}:
        errors.append("UNSUPPORTED_EXECUTION_STATUS")

    if status == "NOT_RUN":
        verdict = "FAIL_OVERCLAIMED_PASS" if _claim_is_true(data) else "NOT_RUN"
        if verdict == "FAIL_OVERCLAIMED_PASS":
            errors.append("UNOBSERVED_PILOT_CANNOT_CLAIM_PASS")
        return {
            "schema_version": 1,
            "pilot_id": str(data.get("pilot_id") or ""),
            "pilot_type": pilot_type,
            "execution_status": status,
            "verdict": verdict,
            "empirical_pass": False,
            "errors": errors,
        }

    _required_text(data, "pilot_id", errors)
    _required_text(data, "observed_at", errors)
    _required_text(data, "observer", errors)

    criteria_pass = False
    if pilot_type == "EXTERNAL_AGENT_TAILORING_SEMANTIC_EQUIVALENCE":
        criteria_pass = _validate_external_agent(data, errors)
    elif pilot_type == "HUMAN_FIRST_USE":
        criteria_pass = _validate_human_first_use(data, errors)
    elif pilot_type == "BROWNFIELD_RECONCILIATION":
        criteria_pass = _validate_brownfield(data, errors)

    claimed = _claim_is_true(data)
    if errors:
        verdict = "FAIL_OVERCLAIMED_PASS" if claimed else "FAIL_INSUFFICIENT_EVIDENCE"
        empirical_pass = False
    elif claimed and not criteria_pass:
        errors.append("OBSERVED_RESULT_DOES_NOT_SUPPORT_PASS_CLAIM")
        verdict = "FAIL_OVERCLAIMED_PASS"
        empirical_pass = False
    elif criteria_pass:
        verdict = "PASS_OBSERVED_EMPIRICAL_PILOT"
        empirical_pass = True
    else:
        verdict = "FAIL_OBSERVED_EMPIRICAL_PILOT"
        empirical_pass = False

    return {
        "schema_version": 1,
        "pilot_id": str(data.get("pilot_id") or ""),
        "pilot_type": pilot_type,
        "execution_status": status,
        "verdict": verdict,
        "empirical_pass": empirical_pass,
        "errors": errors,
        "production_ready_claimed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate empirical pilot evidence.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        result = validate(load_json(Path(args.input)))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"verdict": "FAIL_INSUFFICIENT_EVIDENCE", "error": str(exc)}, ensure_ascii=False))
        return 2
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] in {"NOT_RUN", "PASS_OBSERVED_EMPIRICAL_PILOT", "FAIL_OBSERVED_EMPIRICAL_PILOT"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
