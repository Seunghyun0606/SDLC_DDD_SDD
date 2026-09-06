#!/usr/bin/env python3
"""Typed Change Level + semantic execution policy runtime.

Free text is used only to produce candidate hints. Effective Change Level is based on typed facts,
structural evidence and explicit observed evidence. A level selects semantic work/evidence/review
before Artifact Projection; it is not just a document-count label.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEVELS = ["L1", "L2", "L3", "L4", "L5"]
POLICY_PATH = "sdlc/config/change-execution-policy.json"
STATE_ROOT = "sdlc/runtime/change-level"

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
    policy = load_json(root / POLICY_PATH)
    if not policy.get("levels"):
        raise ValueError(f"change execution policy missing or invalid: {POLICY_PATH}")
    return policy


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
    """Candidate-only signals. They never directly raise Change Level."""
    lowered = text.lower()
    hints: list[str] = []
    patterns = {
        "HAS_INTERFACE": ["interface", "external api", "연계", "kafka", "rest"],
        "HAS_BATCH": ["batch", "배치"],
        "SECURITY_IMPACT": ["security", "privacy", "개인정보", "보안", "권한"],
        "TRANSACTION_IMPACT": ["transaction", "트랜잭션"],
        "ARCHITECTURE_IMPACT": ["architecture", "아키텍처", "platform migration"],
    }
    negative = ["없음", "없다", "no impact", "none", "not affected", "영향 없음"]
    for fact, keys in patterns.items():
        if any(key in lowered for key in keys):
            negated = any(n in lowered for n in negative)
            hints.append(f"{fact}:{'NEGATED_TEXT_CANDIDATE' if negated else 'TEXT_CANDIDATE'}")
    return hints


def _normalize_enum(value: Any, allowed: set[str], default: str) -> str:
    text = str(value if value is not None else default).strip().upper()
    return text if text in allowed else default


def derive_typed_facts(store: dict[str, Any], target: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = extra or {}
    entities = store.get("entities") or {}
    distances = _distances(store, target)
    related = [entities.get(entity_id, {}) for entity_id in distances]
    entity = entities.get(target, {})
    fields = entity.get("fields") or {}
    typed = fields.get("change_facts") if isinstance(fields.get("change_facts"), dict) else {}
    extra_facts = extra.get("facts") if isinstance(extra.get("facts"), dict) else {}

    components = [x for x in related if str(x.get("entity_type") or "").upper() in {"PGM", "PROGRAM", "TASK", "ART"}]
    domains = {str((x.get("fields") or {}).get("domain") or "").strip() for x in related if str((x.get("fields") or {}).get("domain") or "").strip()}
    facts = dict(FACT_DEFAULTS)
    facts["CHANGED_COMPONENT_COUNT"] = len(components)
    facts["CROSS_DOMAIN_COUNT"] = len(domains)

    # Structural entity types are typed evidence. They may establish a business-rule relation,
    # but text cannot establish interface/security/batch/etc. as a fact.
    types = {str(x.get("entity_type") or "").upper() for x in related}
    if types & {"BR", "PROC", "SCN"}:
        facts["BUSINESS_RULE_IMPACT"] = "LOCAL"

    for source in (typed, extra_facts):
        for key, value in source.items():
            facts[str(key).upper()] = value

    # Backward-compatible explicit evidence fields are treated as explicit observations, not text.
    legacy_map = {
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
    for old, new in legacy_map.items():
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
    facts["HAS_INTERFACE"] = _normalize_enum(facts.get("HAS_INTERFACE"), {"YES", "NO", "UNKNOWN"}, "UNKNOWN")
    facts["HAS_BATCH"] = _normalize_enum(facts.get("HAS_BATCH"), {"YES", "NO", "UNKNOWN"}, "UNKNOWN")
    for key in ["BUSINESS_RULE_IMPACT", "TRANSACTION_IMPACT", "SECURITY_IMPACT", "ARCHITECTURE_IMPACT", "MIGRATION_IMPACT"]:
        facts[key] = _normalize_enum(facts.get(key), {"NONE", "LOCAL", "MATERIAL", "UNKNOWN"}, "UNKNOWN" if key not in {"BUSINESS_RULE_IMPACT"} else "NONE")
    facts["SCHEMA_CHANGE"] = _normalize_enum(facts.get("SCHEMA_CHANGE"), {"NONE", "LOCAL", "BREAKING", "UNKNOWN"}, "UNKNOWN")
    facts["OPERATIONAL_RISK"] = _normalize_enum(facts.get("OPERATIONAL_RISK"), {"NORMAL", "HIGH", "UNKNOWN"}, "UNKNOWN")
    facts["IMPACT_COVERAGE"] = _normalize_enum(facts.get("IMPACT_COVERAGE"), {"COMPLETE", "PARTIAL", "UNKNOWN"}, "UNKNOWN")
    facts["PROCESS_COMPLEXITY"] = _normalize_enum(facts.get("PROCESS_COMPLEXITY"), {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}, "UNKNOWN")

    raw_text = _text(entity) + " " + " ".join(_text(x) for x in related)
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

    def enum_points(key: str, mapping: dict[str, int]) -> None:
        nonlocal score
        value = str(facts.get(key) or "UNKNOWN").upper()
        if value == "UNKNOWN":
            uncertain.append(key)
        points = mapping.get(value, 0)
        if points:
            score += points; reasons.append(f"{key}={value}(+{points})")

    enum_points("BUSINESS_RULE_IMPACT", {"LOCAL": 1, "MATERIAL": 2})
    enum_points("HAS_INTERFACE", {"YES": 2})
    enum_points("HAS_BATCH", {"YES": 2})
    enum_points("SCHEMA_CHANGE", {"LOCAL": 2, "BREAKING": 4})
    enum_points("TRANSACTION_IMPACT", {"LOCAL": 1, "MATERIAL": 2})
    enum_points("SECURITY_IMPACT", {"LOCAL": 2, "MATERIAL": 4})
    enum_points("ARCHITECTURE_IMPACT", {"LOCAL": 3, "MATERIAL": 6})
    enum_points("MIGRATION_IMPACT", {"LOCAL": 2, "MATERIAL": 5})
    enum_points("OPERATIONAL_RISK", {"HIGH": 2})
    enum_points("IMPACT_COVERAGE", {"PARTIAL": 2})
    enum_points("PROCESS_COMPLEXITY", {"MEDIUM": 1, "HIGH": 3})

    if score <= 1:
        level = "L1"
    elif score <= 3:
        level = "L2"
    elif score <= 7:
        level = "L3"
    elif score <= 11:
        level = "L4"
    else:
        level = "L5"

    floor = "L1"
    if str(facts.get("ARCHITECTURE_IMPACT")).upper() == "MATERIAL" or str(facts.get("MIGRATION_IMPACT")).upper() == "MATERIAL":
        floor = "L5"; reasons.append("MATERIAL_ARCH_OR_MIGRATION=>L5_FLOOR")
    elif str(facts.get("SECURITY_IMPACT")).upper() == "MATERIAL":
        floor = "L4"; reasons.append("SECURITY_IMPACT=MATERIAL=>L4_FLOOR")
    elif domains >= 2 and (str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES"):
        floor = "L4"; reasons.append("CROSS_DOMAIN_WITH_INTERFACE_OR_BATCH=>L4_FLOOR")
    elif count >= 3 or str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES" or str(facts.get("SCHEMA_CHANGE")).upper() in {"LOCAL", "BREAKING"}:
        floor = "L3"
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


def _state_path(root: Path, target: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", target).strip("_") or "TARGET"
    return root / STATE_ROOT / f"{safe}.json"


def _evidence_path(root: Path, target: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", target).strip("_") or "TARGET"
    return root / STATE_ROOT / f"{safe}-evidence.json"


def resolve_change(root: Path, target: str, store: dict[str, Any], project: dict[str, Any], *, phase: str = "TRIAGE") -> dict[str, Any]:
    previous = load_json(_state_path(root, target))
    extra = load_json(_evidence_path(root, target))
    evidence = derive_typed_facts(store, target, extra)
    classification = classify_typed_facts(evidence)
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
        history.append({"from": effective, "to": observed, "detected_at": now(), "reason": classification["classification_reason"], "evidence_refs": classification["evidence_refs"]})
        effective = observed
    elif LEVELS.index(observed) < LEVELS.index(effective):
        classification["classification_reason"] = list(classification["classification_reason"]) + [f"automatic downgrade blocked: observed {observed}, retained {effective}"]

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
    bpmn = str(row.get("bpmn") or "OFF")
    triggers: list[str] = []
    if str(facts.get("HAS_BATCH")).upper() == "YES": triggers.append("TIMER_OR_BATCH")
    if str(facts.get("HAS_INTERFACE")).upper() == "YES": triggers.append("CROSS_SYSTEM_MESSAGE")
    if int(facts.get("CROSS_DOMAIN_COUNT") or 0) >= 2: triggers.append("CROSS_DOMAIN_PROCESS")
    if str(facts.get("PROCESS_COMPLEXITY")).upper() == "HIGH": triggers.append("EXCEPTION_HEAVY")
    bpmn_required = level in {"L4", "L5"} and bool(triggers)
    return {
        "policy_id": policy.get("policy_id"),
        "change_level": level,
        "fast_path": level in {"L1", "L2"},
        "default_entry_stage": row["default_entry_stage"],
        "required_semantic_work": list(row["semantic_work"]),
        "required_evidence": list(row["required_evidence"]),
        "required_human_review": list(row["required_human_review"]),
        "stage_allowlist": list(row["stage_allowlist"]),
        "program_spec_mode": row["program_spec_mode"],
        "bpmn_policy": bpmn,
        "bpmn_triggers": triggers,
        "bpmn_required": bpmn_required,
        "skipped_stage_is_failure": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["classify", "plan"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    store = load_json(root / "sdlc/canonical/store.json", {"revision": 0, "entities": {}, "relations": []})
    try:
        # This CLI intentionally reads only the small project setting needed here.
        project: dict[str, Any] = {}
        project_path = root / ".sdlc/project.yaml"
        if project_path.is_file():
            # Avoid adding a YAML dependency here; runtime_config_v19 remains the official parser.
            import importlib.util
            spec = importlib.util.spec_from_file_location("change_exec_config", Path(__file__).resolve().parent / "runtime_config_v19.py")
            mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
            project = mod.resolve_runtime_config(root).get("project") or {}
        state = resolve_change(root, args.target, store, project)
        result: dict[str, Any] = {"status": "CLASSIFIED", "change_level": state}
        if args.command == "plan":
            result = {"status": "EXECUTION_PLAN_READY", "change_level": state, "execution_policy": resolve_execution_plan(root, state)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
