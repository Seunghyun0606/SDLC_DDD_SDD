#!/usr/bin/env python3
"""Typed Change Level and semantic execution policy.

This module deliberately stays small. Free text may produce search hints, but final Change Level is
based on typed/structural evidence. Change Level selects semantic work and review depth; it does not
mean that L1/L2 may skip requirement intent, AS-IS source analysis, or impact checking.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LEVELS = ["L1", "L2", "L3", "L4", "L5"]
POLICY_PATH = "sdlc/config/change-execution-policy.json"
STATE_ROOT = "sdlc/runtime/change-level"
CRITICAL_UNKNOWN_FOR_L1 = {"HAS_INTERFACE", "HAS_BATCH", "IMPACT_COVERAGE"}

FACT_DEFAULTS: dict[str, Any] = {
    "CHANGED_COMPONENT_COUNT": 0,
    "CROSS_DOMAIN_COUNT": 0,
    "BUSINESS_RULE_IMPACT": "NONE",
    "HAS_INTERFACE": "UNKNOWN",
    "HAS_BATCH": "UNKNOWN",
    "SCHEMA_CHANGE": "NONE",
    "TRANSACTION_IMPACT": "NONE",
    "SECURITY_IMPACT": "NONE",
    "ARCHITECTURE_IMPACT": "NONE",
    "MIGRATION_IMPACT": "NONE",
    "OPERATIONAL_RISK": "NORMAL",
    "IMPACT_COVERAGE": "UNKNOWN",
    "PROCESS_COMPLEXITY": "LOW",
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return dict(default or {})
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def load_policy(root: Path) -> dict[str, Any]:
    # Project scaffold first, packaged framework config second. The fallback keeps unit/tool usage
    # simple without adding a second policy system.
    for path in [root / POLICY_PATH, HERE.parent / "config/change-execution-policy.json"]:
        if path.is_file():
            policy = load_json(path)
            if isinstance(policy.get("levels"), dict) and policy["levels"]:
                return policy
    raise ValueError(f"change execution policy missing or invalid: {POLICY_PATH}")


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    return str(value or "")


def _distances(store: dict[str, Any], target: str, max_hops: int = 4) -> dict[str, int]:
    entities = store.get("entities") or {}
    if target not in entities:
        return {}
    adjacency: dict[str, set[str]] = {}
    for rel in store.get("relations") or []:
        left, right = str(rel.get("from") or ""), str(rel.get("to") or "")
        if left and right:
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
    out = {target: 0}
    queue = [target]
    while queue:
        current = queue.pop(0)
        if out[current] >= max_hops:
            continue
        for nxt in sorted(adjacency.get(current, set())):
            if nxt not in out:
                out[nxt] = out[current] + 1
                queue.append(nxt)
    return out


def _candidate_hints(text: str) -> list[str]:
    """Keyword matches are retrieval candidates only, never final typed facts."""
    lowered = text.lower()
    patterns = {
        "HAS_INTERFACE": ["interface", "external api", "연계", "kafka", "rest"],
        "HAS_BATCH": ["batch", "배치"],
        "SECURITY_IMPACT": ["security", "privacy", "개인정보", "보안", "권한"],
        "TRANSACTION_IMPACT": ["transaction", "트랜잭션"],
        "ARCHITECTURE_IMPACT": ["architecture", "아키텍처", "platform migration"],
    }
    negative = ["없음", "없다", "no impact", "none", "not affected", "영향 없음"]
    hints: list[str] = []
    for fact, keys in patterns.items():
        if any(key in lowered for key in keys):
            suffix = "NEGATED_TEXT_CANDIDATE" if any(x in lowered for x in negative) else "TEXT_CANDIDATE"
            hints.append(f"{fact}:{suffix}")
    return hints


def _enum(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value if value is not None else default).strip().upper()
    return normalized if normalized in allowed else default


def derive_typed_facts(
    store: dict[str, Any], target: str, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    extra = extra or {}
    entities = store.get("entities") or {}
    distances = _distances(store, target)
    related = [entities.get(entity_id, {}) for entity_id in distances]
    entity = entities.get(target, {})
    fields = entity.get("fields") or {}
    typed = fields.get("change_facts") if isinstance(fields.get("change_facts"), dict) else {}
    extra_facts = extra.get("facts") if isinstance(extra.get("facts"), dict) else {}

    components = [
        row for row in related
        if str(row.get("entity_type") or "").upper() in {"PGM", "PROGRAM", "TASK", "ART"}
    ]
    domains = {
        str((row.get("fields") or {}).get("domain") or "").strip()
        for row in related
        if str((row.get("fields") or {}).get("domain") or "").strip()
    }

    facts = dict(FACT_DEFAULTS)
    facts["CHANGED_COMPONENT_COUNT"] = len(components)
    facts["CROSS_DOMAIN_COUNT"] = len(domains)
    if {str(row.get("entity_type") or "").upper() for row in related} & {"BR", "PROC", "SCN"}:
        facts["BUSINESS_RULE_IMPACT"] = "LOCAL"

    for source in (typed, extra_facts):
        for key, value in source.items():
            facts[str(key).upper()] = value

    # Explicit legacy evidence fields remain supported. Unlike free text, these are caller-provided
    # observations and therefore may be normalized into typed facts.
    legacy = {
        "changed_component_count": "CHANGED_COMPONENT_COUNT",
        "cross_domain_count": "CROSS_DOMAIN_COUNT",
        "business_rule_impact": "BUSINESS_RULE_IMPACT",
        "external_interface": "HAS_INTERFACE",
        "batch": "HAS_BATCH",
        "data_or_schema_change": "SCHEMA_CHANGE",
        "transaction": "TRANSACTION_IMPACT",
        "security_or_privacy": "SECURITY_IMPACT",
        "architecture_change": "ARCHITECTURE_IMPACT",
        "operational_risk": "OPERATIONAL_RISK",
    }
    for old, new in legacy.items():
        if old not in extra:
            continue
        value = extra[old]
        if new in {"CHANGED_COMPONENT_COUNT", "CROSS_DOMAIN_COUNT"}:
            facts[new] = int(value or 0)
        elif new in {"HAS_INTERFACE", "HAS_BATCH"}:
            facts[new] = "YES" if bool(value) else "NO"
        elif new == "SCHEMA_CHANGE":
            facts[new] = "LOCAL" if bool(value) else "NONE"
        elif new in {"BUSINESS_RULE_IMPACT", "TRANSACTION_IMPACT", "SECURITY_IMPACT", "ARCHITECTURE_IMPACT"}:
            facts[new] = "MATERIAL" if bool(value) else "NONE"
        else:
            facts[new] = value
    if "brownfield_impact_coverage_uncertainty" in extra:
        facts["IMPACT_COVERAGE"] = "PARTIAL" if bool(extra["brownfield_impact_coverage_uncertainty"]) else "COMPLETE"

    facts["CHANGED_COMPONENT_COUNT"] = max(0, int(facts.get("CHANGED_COMPONENT_COUNT") or 0))
    facts["CROSS_DOMAIN_COUNT"] = max(0, int(facts.get("CROSS_DOMAIN_COUNT") or 0))
    facts["HAS_INTERFACE"] = _enum(facts.get("HAS_INTERFACE"), {"YES", "NO", "UNKNOWN"}, "UNKNOWN")
    facts["HAS_BATCH"] = _enum(facts.get("HAS_BATCH"), {"YES", "NO", "UNKNOWN"}, "UNKNOWN")
    for key in [
        "BUSINESS_RULE_IMPACT", "TRANSACTION_IMPACT", "SECURITY_IMPACT",
        "ARCHITECTURE_IMPACT", "MIGRATION_IMPACT",
    ]:
        facts[key] = _enum(facts.get(key), {"NONE", "LOCAL", "MATERIAL", "UNKNOWN"}, "NONE")
    facts["SCHEMA_CHANGE"] = _enum(facts.get("SCHEMA_CHANGE"), {"NONE", "LOCAL", "BREAKING", "UNKNOWN"}, "UNKNOWN")
    facts["OPERATIONAL_RISK"] = _enum(facts.get("OPERATIONAL_RISK"), {"NORMAL", "HIGH", "UNKNOWN"}, "UNKNOWN")
    facts["IMPACT_COVERAGE"] = _enum(facts.get("IMPACT_COVERAGE"), {"COMPLETE", "PARTIAL", "UNKNOWN"}, "UNKNOWN")
    facts["PROCESS_COMPLEXITY"] = _enum(facts.get("PROCESS_COMPLEXITY"), {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}, "UNKNOWN")

    raw_text = _text(entity) + " " + " ".join(_text(row) for row in related)
    refs = sorted(set(str(x) for x in list(distances) + list(extra.get("evidence_refs") or [])))
    return {
        "facts": facts,
        "candidate_hints": _candidate_hints(raw_text),
        "evidence_refs": refs,
        "fact_sources": {
            "canonical_structure": bool(distances),
            "canonical_typed_fields": bool(typed),
            "runtime_typed_evidence": bool(extra_facts),
            "free_text_is_candidate_only": True,
        },
    }


def classify_typed_facts(evidence: dict[str, Any]) -> dict[str, Any]:
    facts = evidence.get("facts") if isinstance(evidence.get("facts"), dict) else dict(evidence)
    score = 0
    reasons: list[str] = []
    uncertain: list[str] = []
    count = int(facts.get("CHANGED_COMPONENT_COUNT") or 0)
    domains = int(facts.get("CROSS_DOMAIN_COUNT") or 0)

    if count >= 5:
        score += 4; reasons.append(f"CHANGED_COMPONENT_COUNT={count}(+4)")
    elif count >= 3:
        score += 3; reasons.append(f"CHANGED_COMPONENT_COUNT={count}(+3)")
    elif count == 2:
        score += 1; reasons.append("CHANGED_COMPONENT_COUNT=2(+1)")
    if domains >= 2:
        score += 2; reasons.append(f"CROSS_DOMAIN_COUNT={domains}(+2)")

    mappings = {
        "BUSINESS_RULE_IMPACT": {"LOCAL": 1, "MATERIAL": 2},
        "HAS_INTERFACE": {"YES": 2},
        "HAS_BATCH": {"YES": 2},
        "SCHEMA_CHANGE": {"LOCAL": 2, "BREAKING": 4},
        "TRANSACTION_IMPACT": {"LOCAL": 1, "MATERIAL": 2},
        "SECURITY_IMPACT": {"LOCAL": 2, "MATERIAL": 4},
        "ARCHITECTURE_IMPACT": {"LOCAL": 3, "MATERIAL": 6},
        "MIGRATION_IMPACT": {"LOCAL": 2, "MATERIAL": 5},
        "OPERATIONAL_RISK": {"HIGH": 2},
        "IMPACT_COVERAGE": {"PARTIAL": 2},
        "PROCESS_COMPLEXITY": {"MEDIUM": 1, "HIGH": 3},
    }
    for key, mapping in mappings.items():
        value = str(facts.get(key) or "UNKNOWN").upper()
        if value == "UNKNOWN":
            uncertain.append(key)
        points = mapping.get(value, 0)
        if points:
            score += points
            reasons.append(f"{key}={value}(+{points})")

    level = "L1" if score <= 1 else "L2" if score <= 3 else "L3" if score <= 7 else "L4" if score <= 11 else "L5"
    floor = "L1"
    if str(facts.get("ARCHITECTURE_IMPACT")).upper() == "MATERIAL" or str(facts.get("MIGRATION_IMPACT")).upper() == "MATERIAL":
        floor = "L5"; reasons.append("MATERIAL_ARCH_OR_MIGRATION=>L5_FLOOR")
    elif str(facts.get("SECURITY_IMPACT")).upper() == "MATERIAL":
        floor = "L4"; reasons.append("SECURITY_IMPACT=MATERIAL=>L4_FLOOR")
    elif domains >= 2 and (str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES"):
        floor = "L4"; reasons.append("CROSS_DOMAIN_WITH_INTERFACE_OR_BATCH=>L4_FLOOR")
    elif count >= 3 or str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES" or str(facts.get("SCHEMA_CHANGE")).upper() in {"LOCAL", "BREAKING"}:
        floor = "L3"
    if level == "L1" and CRITICAL_UNKNOWN_FOR_L1 & set(uncertain):
        floor = "L2"
        reasons.append("CRITICAL_TYPED_FACT_UNKNOWN=>L2_SAFETY_FLOOR")
    if LEVELS.index(level) < LEVELS.index(floor):
        level = floor

    return {
        "level": level,
        "score": score,
        "classification_reason": reasons or ["typed facts show a single/local change with no elevated factor"],
        "evidence_refs": list(evidence.get("evidence_refs") or []),
        "typed_facts": facts,
        "candidate_hints": list(evidence.get("candidate_hints") or []),
        "uncertainty": sorted(set(uncertain)),
        "free_text_used_for_final_level": False,
    }


def _safe(target: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", target).strip("_") or "TARGET"


def _state_path(root: Path, target: str) -> Path:
    return root / STATE_ROOT / f"{_safe(target)}.json"


def _evidence_path(root: Path, target: str) -> Path:
    return root / STATE_ROOT / f"{_safe(target)}-evidence.json"


def resolve_change(
    root: Path, target: str, store: dict[str, Any], project: dict[str, Any], *, phase: str = "TRIAGE"
) -> dict[str, Any]:
    previous = load_json(_state_path(root, target))
    extra = load_json(_evidence_path(root, target))
    classification = classify_typed_facts(derive_typed_facts(store, target, extra))
    policy_mode = str(((project.get("change") or {}).get("level_policy") or "AUTO")).upper()
    manual = (project.get("change") or {}).get("default_level")

    if policy_mode == "MANUAL" and manual:
        observed = str(manual).upper()
        if observed not in LEVELS:
            raise ValueError(f"invalid manual Change Level: {manual}")
        classification["level"] = observed
        classification["classification_reason"] = ["project manual default"]
    elif policy_mode == "MANUAL" and not previous.get("effective_change_level"):
        return {
            "schema_version": 2,
            "target_id": target,
            "policy": "MANUAL",
            "status": "HUMAN_DECISION_REQUIRED",
            "provisional_change_level": None,
            "effective_change_level": None,
            "classification_reason": ["MANUAL policy requires human level decision"],
            "evidence_refs": classification["evidence_refs"],
            "typed_facts": classification["typed_facts"],
            "candidate_hints": classification["candidate_hints"],
            "uncertainty": classification["uncertainty"],
            "escalation_history": list(previous.get("escalation_history") or []),
        }

    observed = classification["level"]
    effective = str(previous.get("effective_change_level") or observed)
    provisional = str(previous.get("provisional_change_level") or observed)
    history = list(previous.get("escalation_history") or [])
    if LEVELS.index(observed) > LEVELS.index(effective):
        history.append({
            "from": effective,
            "to": observed,
            "detected_at": now(),
            "reason": classification["classification_reason"],
            "evidence_refs": classification["evidence_refs"],
        })
        effective = observed
    elif LEVELS.index(observed) < LEVELS.index(effective):
        classification["classification_reason"] = list(classification["classification_reason"]) + [
            f"automatic downgrade blocked: observed {observed}, retained {effective}"
        ]

    state = {
        "schema_version": 2,
        "target_id": target,
        "policy": policy_mode,
        "phase": phase,
        "status": "CLASSIFIED",
        "provisional_change_level": provisional,
        "effective_change_level": effective,
        "classification_reason": classification["classification_reason"],
        "evidence_refs": classification["evidence_refs"],
        "typed_facts": classification["typed_facts"],
        "candidate_hints": classification["candidate_hints"],
        "uncertainty": classification["uncertainty"],
        "score": classification["score"],
        "free_text_used_for_final_level": False,
        "escalation_history": history,
        "updated_at": now(),
    }
    path = _state_path(root, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def resolve_execution_plan(root: Path, change_state: dict[str, Any]) -> dict[str, Any]:
    level = str(change_state.get("effective_change_level") or change_state.get("provisional_change_level") or "L3").upper()
    if level not in LEVELS:
        raise ValueError(f"unsupported Change Level for execution: {level}")
    policy = load_policy(root)
    row = dict(policy["levels"][level])
    facts = change_state.get("typed_facts") or {}
    triggers: list[str] = []
    if str(facts.get("HAS_BATCH")).upper() == "YES":
        triggers.append("TIMER_OR_BATCH")
    if str(facts.get("HAS_INTERFACE")).upper() == "YES":
        triggers.append("CROSS_SYSTEM_MESSAGE")
    if int(facts.get("CROSS_DOMAIN_COUNT") or 0) >= 2:
        triggers.append("CROSS_DOMAIN_PROCESS")
    if str(facts.get("PROCESS_COMPLEXITY")).upper() == "HIGH":
        triggers.append("EXCEPTION_HEAVY")

    return {
        "policy_id": policy.get("policy_id"),
        "change_level": level,
        "fast_path": level in {"L1", "L2"},
        "default_entry_stage": row["default_entry_stage"],
        "required_semantic_work": list(row["semantic_work"]),
        "required_evidence": list(row["required_evidence"]),
        "source_write_preconditions": list(row.get("source_write_preconditions") or []),
        "required_human_review": list(row["required_human_review"]),
        "stage_allowlist": list(row["stage_allowlist"]),
        "program_spec_mode": row["program_spec_mode"],
        "bpmn_policy": row.get("bpmn", "OFF"),
        "bpmn_triggers": triggers,
        "bpmn_required": level in {"L4", "L5"} and bool(triggers),
        "skipped_stage_is_failure": False,
        "fast_path_skips_stage_documents_not_semantic_analysis": level in {"L1", "L2"},
    }


def _project(root: Path) -> dict[str, Any]:
    path = HERE / "runtime_config_v19.py"
    spec = importlib.util.spec_from_file_location("change_exec_config", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.resolve_runtime_config(root).get("project") or {} if (root / ".sdlc/project.yaml").is_file() else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["classify", "plan"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    store = load_json(root / "sdlc/canonical/store.json", {"revision": 0, "entities": {}, "relations": []})
    try:
        state = resolve_change(root, args.target, store, _project(root))
        result: dict[str, Any] = {"status": "CLASSIFIED", "change_level": state}
        if args.command == "plan":
            result = {
                "status": "EXECUTION_PLAN_READY",
                "change_level": state,
                "execution_policy": resolve_execution_plan(root, state),
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
