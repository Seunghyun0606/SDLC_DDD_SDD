#!/usr/bin/env python3
"""Typed Change Level and semantic execution policy.

Change Level selects semantic work/evidence/review depth. It does not own Human Artifact topology.
AUTO classification remains evidence based; project/target/human overrides are explicit control-plane
inputs and every effective-level transition is persisted per target.
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


def _save_state(root: Path, target: str, state: dict[str, Any]) -> None:
    path = _state_path(root, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_policy(root: Path) -> dict[str, Any]:
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


def derive_typed_facts(store: dict[str, Any], target: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = extra or {}
    entities = store.get("entities") or {}
    distances = _distances(store, target)
    related = [entities.get(entity_id, {}) for entity_id in distances]
    entity = entities.get(target, {})
    fields = entity.get("fields") or {}
    typed = fields.get("change_facts") if isinstance(fields.get("change_facts"), dict) else {}
    extra_facts = extra.get("facts") if isinstance(extra.get("facts"), dict) else {}

    components = [row for row in related if str(row.get("entity_type") or "").upper() in {"PGM", "PROGRAM", "TASK", "ART"}]
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
    for key in ["BUSINESS_RULE_IMPACT", "TRANSACTION_IMPACT", "SECURITY_IMPACT", "ARCHITECTURE_IMPACT", "MIGRATION_IMPACT"]:
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


def _safety_floor(facts: dict[str, Any], uncertainty: list[str] | set[str] | None = None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    count = int(facts.get("CHANGED_COMPONENT_COUNT") or 0)
    domains = int(facts.get("CROSS_DOMAIN_COUNT") or 0)
    floor = "L1"
    if str(facts.get("ARCHITECTURE_IMPACT")).upper() == "MATERIAL" or str(facts.get("MIGRATION_IMPACT")).upper() == "MATERIAL":
        floor = "L5"; reasons.append("MATERIAL_ARCH_OR_MIGRATION=>L5_FLOOR")
    elif str(facts.get("SECURITY_IMPACT")).upper() == "MATERIAL":
        floor = "L4"; reasons.append("SECURITY_IMPACT=MATERIAL=>L4_FLOOR")
    elif domains >= 2 and (str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES"):
        floor = "L4"; reasons.append("CROSS_DOMAIN_WITH_INTERFACE_OR_BATCH=>L4_FLOOR")
    elif count >= 3 or str(facts.get("HAS_INTERFACE")).upper() == "YES" or str(facts.get("HAS_BATCH")).upper() == "YES" or str(facts.get("SCHEMA_CHANGE")).upper() in {"LOCAL", "BREAKING"}:
        floor = "L3"; reasons.append("COMPONENT_INTERFACE_BATCH_OR_SCHEMA=>L3_FLOOR")
    unknown = set(uncertainty or [])
    if floor == "L1" and CRITICAL_UNKNOWN_FOR_L1 & unknown:
        floor = "L2"; reasons.append("CRITICAL_TYPED_FACT_UNKNOWN=>L2_SAFETY_FLOOR")
    return floor, reasons


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
        "BUSINESS_RULE_IMPACT": {"LOCAL": 1, "MATERIAL": 2}, "HAS_INTERFACE": {"YES": 2},
        "HAS_BATCH": {"YES": 2}, "SCHEMA_CHANGE": {"LOCAL": 2, "BREAKING": 4},
        "TRANSACTION_IMPACT": {"LOCAL": 1, "MATERIAL": 2}, "SECURITY_IMPACT": {"LOCAL": 2, "MATERIAL": 4},
        "ARCHITECTURE_IMPACT": {"LOCAL": 3, "MATERIAL": 6}, "MIGRATION_IMPACT": {"LOCAL": 2, "MATERIAL": 5},
        "OPERATIONAL_RISK": {"HIGH": 2}, "IMPACT_COVERAGE": {"PARTIAL": 2}, "PROCESS_COMPLEXITY": {"MEDIUM": 1, "HIGH": 3},
    }
    for key, mapping in mappings.items():
        value = str(facts.get(key) or "UNKNOWN").upper()
        if value == "UNKNOWN": uncertain.append(key)
        points = mapping.get(value, 0)
        if points:
            score += points; reasons.append(f"{key}={value}(+{points})")
    scored = "L1" if score <= 1 else "L2" if score <= 3 else "L3" if score <= 7 else "L4" if score <= 11 else "L5"
    floor, floor_reasons = _safety_floor(facts, uncertain)
    level = floor if LEVELS.index(scored) < LEVELS.index(floor) else scored
    reasons.extend(x for x in floor_reasons if x not in reasons)
    return {
        "level": level,
        "scored_level": scored,
        "safety_floor": floor,
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


def _target_config(change: dict[str, Any], target: str) -> dict[str, Any] | None:
    rows = change.get("target_levels") or {}
    if not isinstance(rows, dict) or target not in rows:
        return None
    raw = rows[target]
    if isinstance(raw, str):
        return {"level": raw, "reason": "project target override"}
    if not isinstance(raw, dict):
        raise ValueError(f"change.target_levels.{target} must be a level string or mapping")
    return dict(raw)


def _level(value: Any, label: str) -> str:
    level = str(value or "").upper()
    if level not in LEVELS:
        raise ValueError(f"{label} must be one of L1..L5")
    return level


def _append_history(history: list[dict[str, Any]], *, old: str | None, new: str | None, source: str, reason: Any,
                    safety_floor: str, risk_accepted: bool = False, requested_by: str | None = None) -> None:
    signature = (old, new, source, json.dumps(reason, ensure_ascii=False, sort_keys=True), bool(risk_accepted))
    if history:
        last = history[-1]
        last_sig = (last.get("from"), last.get("to"), last.get("source"), json.dumps(last.get("reason"), ensure_ascii=False, sort_keys=True), bool(last.get("risk_accepted")))
        if signature == last_sig:
            return
    row: dict[str, Any] = {
        "at": now(), "from": old, "to": new, "source": source, "reason": reason,
        "safety_floor": safety_floor, "risk_accepted": bool(risk_accepted),
    }
    if requested_by: row["requested_by"] = requested_by
    history.append(row)


def set_human_override(root: Path, target: str, level: str, reason: str, *, requested_by: str = "USER",
                       accept_below_safety_floor: bool = False, store: dict[str, Any] | None = None,
                       project: dict[str, Any] | None = None) -> dict[str, Any]:
    if not reason.strip():
        raise ValueError("human Change Level override requires --reason")
    desired = _level(level, "human override level")
    store = store or load_json(root / "sdlc/canonical/store.json", {"revision": 0, "entities": {}, "relations": []})
    evidence = classify_typed_facts(derive_typed_facts(store, target, load_json(_evidence_path(root, target))))
    floor = str(evidence["safety_floor"])
    if LEVELS.index(desired) < LEVELS.index(floor) and not accept_below_safety_floor:
        raise ValueError(f"requested {desired} is below safety floor {floor}; explicit risk acceptance is required")
    previous = load_json(_state_path(root, target))
    history = list(previous.get("level_history") or [])
    old = previous.get("effective_change_level")
    _append_history(history, old=str(old) if old else None, new=desired, source="HUMAN_OVERRIDE", reason=reason,
                    safety_floor=floor, risk_accepted=accept_below_safety_floor, requested_by=requested_by)
    previous.update({
        "schema_version": 3,
        "target_id": target,
        "human_override": {"level": desired, "reason": reason, "requested_by": requested_by,
                           "accepted_below_safety_floor": bool(accept_below_safety_floor), "set_at": now()},
        "level_history": history,
        "rebaseline_requested": False,
    })
    _save_state(root, target, previous)
    return resolve_change(root, target, store, project or {}, phase="HUMAN_OVERRIDE")


def clear_human_override(root: Path, target: str, reason: str, *, requested_by: str = "USER") -> dict[str, Any]:
    previous = load_json(_state_path(root, target))
    if not previous.get("human_override"):
        return previous
    history = list(previous.get("level_history") or [])
    _append_history(history, old=str(previous.get("effective_change_level") or "") or None, new=None,
                    source="HUMAN_OVERRIDE_CLEARED", reason=reason or "return to project/AUTO policy",
                    safety_floor=str(previous.get("safety_floor") or "L1"), requested_by=requested_by)
    previous.pop("human_override", None)
    previous["level_history"] = history
    previous["rebaseline_requested"] = True
    previous["updated_at"] = now()
    _save_state(root, target, previous)
    return previous


def resolve_change(root: Path, target: str, store: dict[str, Any], project: dict[str, Any], *, phase: str = "TRIAGE") -> dict[str, Any]:
    previous = load_json(_state_path(root, target))
    extra = load_json(_evidence_path(root, target))
    classification = classify_typed_facts(derive_typed_facts(store, target, extra))
    auto_observed = str(classification["level"])
    floor = str(classification["safety_floor"])
    change = project.get("change") or {}
    if not isinstance(change, dict): raise ValueError("change must be a mapping")
    policy_mode = str(change.get("level_policy") or "AUTO").upper()
    if policy_mode not in {"AUTO", "MANUAL"}: raise ValueError("change.level_policy must be AUTO or MANUAL")

    selected = auto_observed
    source = "AUTO_CLASSIFICATION"
    reason: Any = classification["classification_reason"]
    risk_accepted = False

    minimum = change.get("minimum_level")
    if minimum is not None:
        minimum_level = _level(minimum, "change.minimum_level")
        if LEVELS.index(selected) < LEVELS.index(minimum_level):
            selected = minimum_level; source = "PROJECT_MINIMUM_LEVEL"; reason = f"project minimum level {minimum_level}"

    target_cfg = _target_config(change, target)
    if target_cfg is not None:
        selected = _level(target_cfg.get("level"), f"change.target_levels.{target}.level")
        source = "PROJECT_TARGET_OVERRIDE"
        reason = target_cfg.get("reason") or "project target override"
        risk_accepted = bool(target_cfg.get("accept_below_safety_floor", False))
    elif policy_mode == "MANUAL" and change.get("default_level"):
        selected = _level(change.get("default_level"), "change.default_level")
        source = "PROJECT_MANUAL_DEFAULT"; reason = "project manual default"
    elif policy_mode == "MANUAL" and not previous.get("effective_change_level") and not previous.get("human_override"):
        state = {
            "schema_version": 3, "target_id": target, "policy": "MANUAL", "phase": phase,
            "status": "HUMAN_DECISION_REQUIRED", "provisional_change_level": None, "effective_change_level": None,
            "observed_change_level": auto_observed, "safety_floor": floor,
            "classification_reason": ["MANUAL policy requires human level decision"],
            "evidence_refs": classification["evidence_refs"], "typed_facts": classification["typed_facts"],
            "candidate_hints": classification["candidate_hints"], "uncertainty": classification["uncertainty"],
            "escalation_history": list(previous.get("escalation_history") or []),
            "level_history": list(previous.get("level_history") or []), "updated_at": now(),
        }
        _save_state(root, target, state); return state

    human = previous.get("human_override")
    if isinstance(human, dict) and human.get("level"):
        selected = _level(human.get("level"), "human override level")
        source = "HUMAN_OVERRIDE"; reason = human.get("reason") or "human override"
        risk_accepted = bool(human.get("accepted_below_safety_floor", False))

    if LEVELS.index(selected) < LEVELS.index(floor) and source != "AUTO_CLASSIFICATION" and not risk_accepted:
        raise ValueError(f"{source} selects {selected} below safety floor {floor}; explicit risk acceptance is required")

    old_effective = str(previous.get("effective_change_level") or "") or None
    rebaseline = bool(previous.get("rebaseline_requested"))
    effective = selected
    escalation_history = list(previous.get("escalation_history") or [])
    if source in {"AUTO_CLASSIFICATION", "PROJECT_MINIMUM_LEVEL"} and old_effective and not rebaseline:
        if LEVELS.index(selected) > LEVELS.index(old_effective):
            escalation_history.append({"from": old_effective, "to": selected, "detected_at": now(),
                                       "reason": classification["classification_reason"], "evidence_refs": classification["evidence_refs"]})
        elif LEVELS.index(selected) < LEVELS.index(old_effective):
            effective = old_effective
            reason = list(classification["classification_reason"]) + [f"automatic downgrade blocked: observed {selected}, retained {old_effective}"]
            source = str(previous.get("level_source") or "AUTO_CLASSIFICATION")

    provisional = str(previous.get("provisional_change_level") or selected)
    history = list(previous.get("level_history") or [])
    if old_effective != effective or str(previous.get("level_source") or "") != source:
        _append_history(history, old=old_effective, new=effective, source=source, reason=reason,
                        safety_floor=floor, risk_accepted=risk_accepted,
                        requested_by=(human or {}).get("requested_by") if isinstance(human, dict) else None)

    state = {
        "schema_version": 3, "target_id": target, "policy": policy_mode, "phase": phase, "status": "CLASSIFIED",
        "provisional_change_level": provisional, "observed_change_level": auto_observed,
        "effective_change_level": effective, "level_source": source, "safety_floor": floor,
        "classification_reason": reason, "evidence_refs": classification["evidence_refs"],
        "typed_facts": classification["typed_facts"], "candidate_hints": classification["candidate_hints"],
        "uncertainty": classification["uncertainty"], "score": classification["score"],
        "free_text_used_for_final_level": False, "escalation_history": escalation_history,
        "level_history": history, "human_override": human if isinstance(human, dict) else None,
        "rebaseline_requested": False, "updated_at": now(),
    }
    _save_state(root, target, state)
    return state


def resolve_execution_plan(root: Path, change_state: dict[str, Any]) -> dict[str, Any]:
    level = str(change_state.get("effective_change_level") or change_state.get("provisional_change_level") or "L3").upper()
    if level not in LEVELS: raise ValueError(f"unsupported Change Level for execution: {level}")
    policy = load_policy(root); row = dict(policy["levels"][level]); facts = change_state.get("typed_facts") or {}
    triggers: list[str] = []
    if str(facts.get("HAS_BATCH")).upper() == "YES": triggers.append("TIMER_OR_BATCH")
    if str(facts.get("HAS_INTERFACE")).upper() == "YES": triggers.append("CROSS_SYSTEM_MESSAGE")
    if int(facts.get("CROSS_DOMAIN_COUNT") or 0) >= 2: triggers.append("CROSS_DOMAIN_PROCESS")
    if str(facts.get("PROCESS_COMPLEXITY")).upper() == "HIGH": triggers.append("EXCEPTION_HEAVY")
    return {
        "policy_id": policy.get("policy_id"), "change_level": level, "change_level_source": change_state.get("level_source"),
        "safety_floor": change_state.get("safety_floor"), "fast_path": level in {"L1", "L2"},
        "default_entry_stage": row["default_entry_stage"], "required_semantic_work": list(row["semantic_work"]),
        "required_evidence": list(row["required_evidence"]), "source_write_preconditions": list(row.get("source_write_preconditions") or []),
        "required_human_review": list(row["required_human_review"]), "stage_allowlist": list(row["stage_allowlist"]),
        "program_spec_mode": row["program_spec_mode"], "bpmn_policy": row.get("bpmn", "OFF"), "bpmn_triggers": triggers,
        "bpmn_required": level in {"L4", "L5"} and bool(triggers), "skipped_stage_is_failure": False,
        "fast_path_skips_stage_documents_not_semantic_analysis": level in {"L1", "L2"},
        "change_level_does_not_own_projection_topology": True,
    }


def _project(root: Path) -> dict[str, Any]:
    path = HERE / "runtime_config_v19.py"
    spec = importlib.util.spec_from_file_location("change_exec_config", path)
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
    return mod.resolve_runtime_config(root).get("project") or {} if (root / ".sdlc/project.yaml").is_file() else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["classify", "plan", "show", "set-level", "clear-level"])
    ap.add_argument("--root", default="."); ap.add_argument("--target", required=True)
    ap.add_argument("--level"); ap.add_argument("--reason"); ap.add_argument("--requested-by", default="USER")
    ap.add_argument("--accept-below-safety-floor", action="store_true")
    args = ap.parse_args(argv); root = Path(args.root).resolve()
    store = load_json(root / "sdlc/canonical/store.json", {"revision": 0, "entities": {}, "relations": []})
    try:
        project = _project(root)
        if args.command == "show":
            state = load_json(_state_path(root, args.target)); result = {"status": "CHANGE_LEVEL_STATE", "change_level": state}
        elif args.command == "set-level":
            if not args.level: raise ValueError("--level is required")
            state = set_human_override(root, args.target, args.level, args.reason or "", requested_by=args.requested_by,
                                       accept_below_safety_floor=args.accept_below_safety_floor, store=store, project=project)
            result = {"status": "CHANGE_LEVEL_OVERRIDE_SET", "change_level": state,
                      "next_action": "rerun /work to recalculate semantic work and refresh required projections"}
        elif args.command == "clear-level":
            clear_human_override(root, args.target, args.reason or "return to project/AUTO policy", requested_by=args.requested_by)
            state = resolve_change(root, args.target, store, project, phase="OVERRIDE_CLEARED")
            result = {"status": "CHANGE_LEVEL_OVERRIDE_CLEARED", "change_level": state,
                      "next_action": "rerun /work to refresh projections for the recalculated level"}
        else:
            state = resolve_change(root, args.target, store, project)
            result = {"status": "CLASSIFIED", "change_level": state}
            if args.command == "plan":
                result = {"status": "EXECUTION_PLAN_READY", "change_level": state, "execution_policy": resolve_execution_plan(root, state)}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
