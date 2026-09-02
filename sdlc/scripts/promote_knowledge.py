#!/usr/bin/env python3
"""Promote explicitly reviewed project knowledge without automatic Canonical publish.

Human review may confirm an OBSERVED/INFERRED business-semantic candidate, but the transition to
CONFIRMED is explicit and recorded. Source behavior alone can never perform that transition.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any
import yaml

TRUTH = {"GIVEN", "OBSERVED", "INFERRED", "CONFIRMED", "OPEN"}
PROMOTION = {"CANDIDATE", "REVIEW_REQUIRED", "PROMOTED", "REJECTED", "SUPERSEDED"}


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def _positive_revision(value: Any) -> int | None:
    try:
        number = int(value)
        return number if number >= 1 else None
    except (TypeError, ValueError):
        return None


def validate_candidate(doc: dict[str, Any], config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root = (doc or {}).get("knowledge_candidate") or {}
    allowed_types = set(config.get("allowed_types") or [])
    decisions = set(config.get("review_decisions") or [])
    business_types = set(config.get("business_semantic_types") or [])
    if not root.get("knowledge_id"): errors.append("P1KP-001 knowledge_id required")
    if not root.get("project_id"): errors.append("P1KP-002 project_id required")
    if root.get("type") not in allowed_types: errors.append("P1KP-003 unsupported knowledge type")
    if root.get("truth_state") not in TRUTH: errors.append("P1KP-004 invalid truth_state")
    if root.get("promotion_state") not in PROMOTION: errors.append("P1KP-005 invalid promotion_state")
    if root.get("promotion_state") not in {"CANDIDATE", "REVIEW_REQUIRED"}:
        errors.append("P1KP-006 only CANDIDATE/REVIEW_REQUIRED can be reviewed")
    prov = root.get("provenance") or {}
    if not (prov.get("evidence_ids") or prov.get("source_refs")):
        errors.append("P1KP-007 provenance required")
    if _positive_revision(root.get("revision")) is None:
        errors.append("P1KP-008 positive revision required")
    review = root.get("review") or {}
    decision = review.get("decision")
    if decision not in decisions:
        errors.append("P1KP-009 review.decision must be CONFIRM, REJECT or SUPERSEDE")
        return errors
    for key in ("reviewed_by", "reviewed_at", "decision_basis"):
        if not review.get(key): errors.append(f"P1KP-010 review.{key} required")
    if decision == "CONFIRM":
        if root.get("truth_state") == "OPEN": errors.append("P1KP-011 OPEN knowledge cannot be promoted")
        if root.get("type") in business_types and root.get("truth_state") in {"OBSERVED", "INFERRED"} and review.get("human_confirmation") is not True:
            errors.append("P1KP-012 observed/inferred business semantics require explicit human_confirmation=true")
    if decision == "SUPERSEDE" and not (root.get("relations") or {}).get("supersedes"):
        errors.append("P1KP-013 SUPERSEDE requires relations.supersedes")
    return errors


def _normalized_candidate(candidate_doc: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], str]:
    candidate = deepcopy(candidate_doc["knowledge_candidate"])
    review = candidate.get("review") or {}
    decision = review.get("decision")
    business_types = set(config.get("business_semantic_types") or [])
    if decision == "CONFIRM":
        if candidate.get("type") in business_types and candidate.get("truth_state") in {"OBSERVED", "INFERRED"}:
            candidate["truth_state_before_review"] = candidate.get("truth_state")
            candidate["truth_state"] = "CONFIRMED"
            candidate["truth_confirmation"] = {
                "confirmed_by": review.get("reviewed_by"),
                "confirmed_at": review.get("reviewed_at"),
                "basis": review.get("decision_basis"),
                "human_confirmation": True,
            }
        candidate["promotion_state"] = "PROMOTED"
        state = "PROMOTED"
    elif decision == "REJECT":
        candidate["promotion_state"] = "REJECTED"
        state = "REJECTED"
    else:
        candidate["promotion_state"] = "SUPERSEDED"
        state = "SUPERSEDED"
    candidate["canonical_publish_requested"] = False
    return candidate, state


def promote(candidate_doc: dict[str, Any], registry_doc: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    errors = validate_candidate(candidate_doc, config)
    if errors:
        return registry_doc, {"state": "DENIED", "errors": errors, "canonical_publish_requested": False}
    candidate, state = _normalized_candidate(candidate_doc, config)
    root = deepcopy((registry_doc or {}).get("knowledge_registry") or {})
    entries = list(root.get("entries") or [])
    history = list(root.get("history") or [])
    decisions = list(root.get("decisions") or [])
    kid = candidate["knowledge_id"]
    rev = int(candidate["revision"])
    decision_key = f"{kid}:{rev}:{(candidate.get('review') or {}).get('decision')}"
    previous_decision = next((x for x in decisions if x.get("idempotency_key") == decision_key), None)
    if previous_decision:
        return registry_doc, {"state": "IDEMPOTENT", "knowledge_id": kid, "revision": rev, "decision": (candidate.get("review") or {}).get("decision"), "canonical_publish_requested": False}

    current_idx = next((i for i, x in enumerate(entries) if x.get("knowledge_id") == kid), None)
    if current_idx is not None:
        current = entries[current_idx]
        current_rev = int(current.get("revision") or 0)
        if rev < current_rev:
            return registry_doc, {"state": "DENIED", "errors": ["P1KP-020 stale knowledge revision"], "canonical_publish_requested": False}
        if rev == current_rev and current != candidate:
            return registry_doc, {"state": "DENIED", "errors": ["P1KP-021 same revision has different reviewed result"], "canonical_publish_requested": False}

    record = {
        "idempotency_key": decision_key,
        "knowledge_id": kid,
        "revision": rev,
        "decision": (candidate.get("review") or {}).get("decision"),
        "reviewed_by": (candidate.get("review") or {}).get("reviewed_by"),
        "reviewed_at": (candidate.get("review") or {}).get("reviewed_at"),
        "decision_basis": (candidate.get("review") or {}).get("decision_basis"),
        "result": state,
    }
    decisions.append(record)

    if state == "PROMOTED":
        if current_idx is None:
            entries.append(candidate)
        else:
            current = entries[current_idx]
            if rev > int(current.get("revision") or 0):
                old = deepcopy(current); old["promotion_state"] = "SUPERSEDED"; history.append(old)
                entries[current_idx] = candidate
            else:
                entries[current_idx] = candidate
    else:
        history.append(candidate)
        if state == "SUPERSEDED":
            superseded_ids = set((candidate.get("relations") or {}).get("supersedes") or [])
            for idx, entry in enumerate(entries):
                if entry.get("knowledge_id") in superseded_ids:
                    old = deepcopy(entry); old["promotion_state"] = "SUPERSEDED"; history.append(old)
                    entries[idx] = old

    entries = sorted(entries, key=lambda x: str(x.get("knowledge_id")))
    output = {
        "schema_version": 1,
        "artifact_type": "KNOWLEDGE_REGISTRY",
        "knowledge_registry": {
            "entries": entries,
            "history": history,
            "decisions": decisions,
            "canonical_publish_automatic": False,
        },
    }
    return output, {
        "state": state,
        "knowledge_id": kid,
        "revision": rev,
        "truth_state": candidate.get("truth_state"),
        "canonical_publish_requested": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("candidate", type=Path)
    p.add_argument("--config", type=Path, default=Path("sdlc/config/knowledge-promotion.yaml"))
    p.add_argument("--registry", type=Path, default=Path(".ai-sdlc/knowledge-registry.yaml"))
    p.add_argument("--result", type=Path)
    args = p.parse_args()
    registry, result = promote(load(args.candidate), load(args.registry), load(args.config))
    result_doc = {"schema_version": 1, "artifact_type": "KNOWLEDGE_PROMOTION_RESULT", "knowledge_promotion": result}
    print(yaml.safe_dump(result_doc, allow_unicode=True, sort_keys=False), end="")
    if args.result:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(yaml.safe_dump(result_doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if result["state"] == "DENIED": return 2
    args.registry.parent.mkdir(parents=True, exist_ok=True)
    args.registry.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
