#!/usr/bin/env python3
"""Artifact Tailoring + Change Level runtime for SDLC Harness v1.9.

This layer never removes internal Stages. It decides which Human Artifact receives a Stage's
Canonical/Evidence meaning, and it keeps per-RQ Change Level explainability in runtime state.
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
_spec = importlib.util.spec_from_file_location("tailoring_config_v19", HERE / "runtime_config_v19.py")
CONFIG = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(CONFIG)

STAGES = [
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION",
]
LEVELS = ["L1", "L2", "L3", "L4", "L5"]
LEVEL_NAMES = {"L1": "MICRO", "L2": "LOCAL", "L3": "FEATURE", "L4": "PROCESS", "L5": "ARCH"}
AUDIENCES = {"MACHINE", "INTERNAL_IT", "PM_REVIEW", "CUSTOMER"}
DEFAULT_PROFILES = {
    "internal": "STAGE_ORIENTED_FULL",
    "customer": "CUSTOMER_STANDARD_3",
    "pm": "PM_STANDARD",
}
PROFILE_ROOTS = ["sdlc/custom/project/tailoring", "sdlc/tailoring/standard"]
CHANGE_RUNTIME_ROOT = "sdlc/runtime/change-level"
PROJECTION_RUNTIME_ROOT = "sdlc/runtime/projections"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def load_store(root: Path) -> dict[str, Any]:
    path = root / "sdlc/canonical/store.json"
    if not path.is_file():
        return {"revision": 0, "entities": {}, "relations": []}
    data = load_json(path)
    data.setdefault("revision", 0)
    data.setdefault("entities", {})
    data.setdefault("relations", [])
    return data


def _safe_target(target: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", target).strip("_") or "TARGET"


def _profile_candidates(root: Path, profile_id: str) -> list[Path]:
    names = [profile_id, f"internal-{profile_id}", f"customer-{profile_id}", f"pm-{profile_id}"]
    candidates: list[Path] = []
    for base in PROFILE_ROOTS:
        for name in names:
            for suffix in [".yaml", ".yml", ".json"]:
                path = root / base / f"{name}{suffix}"
                if path not in candidates:
                    candidates.append(path)
    return candidates


def load_profile(root: Path, profile_id: str) -> tuple[dict[str, Any], Path]:
    for path in _profile_candidates(root, profile_id):
        if path.is_file():
            profile = CONFIG.load_config(path)
            validate_profile(profile, root=root, source_path=path)
            return profile, path
    raise ValueError(f"tailoring profile not found: {profile_id}")


def _artifact_rows(profile: dict[str, Any]) -> list[dict[str, Any]]:
    raw = profile.get("artifacts") or {}
    if not isinstance(raw, dict):
        raise ValueError("tailoring artifacts must be a mapping keyed by artifact id")
    rows: list[dict[str, Any]] = []
    for artifact_id, value in raw.items():
        if not isinstance(value, dict):
            raise ValueError(f"artifact {artifact_id} must be a mapping")
        row = dict(value)
        row["id"] = str(artifact_id)
        rows.append(row)
    return rows


def validate_profile(profile: dict[str, Any], *, root: Path | None = None, source_path: Path | None = None) -> None:
    if int(profile.get("schema_version", 0) or 0) != 1:
        raise ValueError(f"tailoring profile schema_version must be 1: {source_path or '<memory>'}")
    profile_id = str(profile.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("tailoring profile_id is required")
    seen: set[str] = set()
    for row in _artifact_rows(profile):
        artifact_id = row["id"]
        if artifact_id in seen:
            raise ValueError(f"duplicate artifact id: {artifact_id}")
        seen.add(artifact_id)
        audience = str(row.get("audience") or "").upper()
        if audience not in AUDIENCES:
            raise ValueError(f"artifact {artifact_id} has unsupported audience: {audience}")
        template = str(row.get("template") or "").strip()
        if not template:
            raise ValueError(f"artifact {artifact_id} template is required")
        sources = row.get("sources") or {}
        if not isinstance(sources, dict):
            raise ValueError(f"artifact {artifact_id} sources must be a mapping")
        stages = sources.get("stages") or []
        if not isinstance(stages, list) or not stages:
            raise ValueError(f"artifact {artifact_id} requires sources.stages")
        unknown = [str(x) for x in stages if str(x).upper() not in STAGES]
        if unknown:
            raise ValueError(f"artifact {artifact_id} has unknown stage(s): {', '.join(unknown)}")
        if root is not None and not (root / template).is_file():
            raise ValueError(f"artifact {artifact_id} template not found: {template}")
        if audience == "CUSTOMER":
            canonical = sources.get("canonical") or []
            upstream = sources.get("artifacts") or []
            if not canonical and not upstream and not stages:
                raise ValueError(f"customer artifact {artifact_id} requires upstream source")


def project_profile_ids(project: dict[str, Any]) -> dict[str, str]:
    return {
        audience: str(CONFIG.nested(project, "documents", audience, "profile", default=default) or default)
        for audience, default in DEFAULT_PROFILES.items()
    }


def _relation_distances(store: dict[str, Any], target: str, max_hops: int = 4) -> dict[str, int]:
    if target not in store.get("entities", {}):
        return {}
    adjacency: dict[str, set[str]] = {}
    for rel in store.get("relations", []):
        left, right = str(rel.get("from") or ""), str(rel.get("to") or "")
        if left and right:
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
    distances = {target: 0}
    frontier = [target]
    while frontier:
        node = frontier.pop(0)
        distance = distances[node]
        if distance >= max_hops:
            continue
        for nxt in sorted(adjacency.get(node, set())):
            if nxt not in distances:
                distances[nxt] = distance + 1
                frontier.append(nxt)
    return distances


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    return str(value or "")


def derive_change_evidence(store: dict[str, Any], target: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    distances = _relation_distances(store, target)
    related = [store.get("entities", {}).get(entity_id, {}) for entity_id in distances]
    entity = store.get("entities", {}).get(target, {})
    all_text = (_text(entity) + " " + " ".join(_text(x) for x in related)).lower()
    types = [str(x.get("entity_type") or "").upper() for x in related]
    components = [x for x in related if str(x.get("entity_type") or "").upper() in {"PGM", "ART", "PROGRAM", "TASK"}]
    domains = {
        str((x.get("fields") or {}).get("domain") or "").strip()
        for x in related
        if str((x.get("fields") or {}).get("domain") or "").strip()
    }
    evidence: dict[str, Any] = {
        "changed_component_count": len(components),
        "business_rule_impact": any(t in {"BR", "PROC", "SCN"} for t in types) or "business rule" in all_text or "업무규칙" in all_text,
        "data_or_schema_change": any(t in {"DATA", "TABLE", "COLUMN"} for t in types) and any(k in all_text for k in ["change", "modify", "schema", "변경", "추가", "삭제"]),
        "external_interface": any(k in all_text for k in ["interface", "external api", "외부", "연계", "kafka", "rest"]),
        "batch": "batch" in all_text or "배치" in all_text,
        "transaction": "transaction" in all_text or "트랜잭션" in all_text,
        "security_or_privacy": any(k in all_text for k in ["security", "privacy", "개인정보", "보안", "권한"]),
        "cross_domain": len(domains) >= 2,
        "operational_risk": "HIGH" if any(k in all_text for k in ["production", "운영위험", "downtime", "장애", "critical"]) else "NORMAL",
        "brownfield_impact_coverage_uncertainty": any(k in all_text for k in ["check_required", "candidate", "coverage gap", "미확정", "불확실"]),
        "architecture_change": any(k in all_text for k in ["architecture change", "아키텍처 변경", "platform migration"]),
        "evidence_refs": sorted(distances),
    }
    if extra:
        for key, value in extra.items():
            if key == "evidence_refs":
                refs = list(evidence.get("evidence_refs") or []) + list(value or [])
                evidence[key] = sorted(set(str(x) for x in refs if str(x)))
            else:
                evidence[key] = value
    return evidence


def classify_change_level(evidence: dict[str, Any]) -> dict[str, Any]:
    component_count = int(evidence.get("changed_component_count") or 0)
    score = 0
    factors: list[str] = []
    if component_count >= 5:
        score += 3; factors.append(f"changed_component_count={component_count}(+3)")
    elif component_count >= 3:
        score += 2; factors.append(f"changed_component_count={component_count}(+2)")
    elif component_count == 2:
        score += 1; factors.append("changed_component_count=2(+1)")
    weighted = [
        ("business_rule_impact", 1), ("data_or_schema_change", 2), ("external_interface", 2),
        ("batch", 2), ("transaction", 1), ("security_or_privacy", 3), ("cross_domain", 2),
        ("brownfield_impact_coverage_uncertainty", 2),
    ]
    for key, points in weighted:
        if bool(evidence.get(key)):
            score += points
            factors.append(f"{key}(+{points})")
    if str(evidence.get("operational_risk") or "").upper() == "HIGH":
        score += 2
        factors.append("operational_risk=HIGH(+2)")

    if score <= 1:
        level = "L1"
    elif score <= 3:
        level = "L2"
    elif score <= 6:
        level = "L3"
    elif score <= 9:
        level = "L4"
    else:
        level = "L5"

    floor = "L1"
    if bool(evidence.get("architecture_change")):
        floor = "L5"
        factors.append("architecture_change=>L5 floor")
    elif bool(evidence.get("security_or_privacy")):
        floor = "L4"
        factors.append("security_or_privacy=>L4 floor")
    elif bool(evidence.get("cross_domain")) and (bool(evidence.get("external_interface")) or bool(evidence.get("batch"))):
        floor = "L4"
        factors.append("cross_domain+interface/batch=>L4 floor")
    elif bool(evidence.get("external_interface")) or bool(evidence.get("batch")) or bool(evidence.get("data_or_schema_change")) or component_count >= 3:
        floor = "L3"
    if LEVELS.index(level) < LEVELS.index(floor):
        level = floor

    return {
        "level": level,
        "name": LEVEL_NAMES[level],
        "score": score,
        "classification_reason": factors or ["single/local change with no elevated factor observed"],
        "evidence_refs": list(evidence.get("evidence_refs") or []),
        "factor_snapshot": {k: v for k, v in evidence.items() if k != "evidence_refs"},
    }


def _change_state_path(root: Path, target: str) -> Path:
    return root / CHANGE_RUNTIME_ROOT / f"{_safe_target(target)}.json"


def load_change_state(root: Path, target: str) -> dict[str, Any]:
    path = _change_state_path(root, target)
    return load_json(path) if path.is_file() else {}


def _optional_change_evidence(root: Path, target: str) -> dict[str, Any]:
    path = root / CHANGE_RUNTIME_ROOT / f"{_safe_target(target)}-evidence.json"
    return load_json(path) if path.is_file() else {}


def resolve_change_level(root: Path, target: str, stage: str, store: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    policy = str(CONFIG.nested(project, "change", "level_policy", default="AUTO") or "AUTO").upper()
    previous = load_change_state(root, target)
    manual_default = CONFIG.nested(project, "change", "default_level", default=None)
    if policy == "MANUAL" and not manual_default and not previous.get("effective_change_level"):
        return {
            "policy": "MANUAL",
            "status": "HUMAN_DECISION_REQUIRED",
            "provisional_change_level": previous.get("provisional_change_level"),
            "effective_change_level": previous.get("effective_change_level"),
            "classification_reason": ["MANUAL policy requires change.default_level or prior human decision"],
            "evidence_refs": [],
            "escalation_history": previous.get("escalation_history", []),
        }

    if policy == "MANUAL" and manual_default:
        classification = {
            "level": str(manual_default).upper(),
            "name": LEVEL_NAMES[str(manual_default).upper()],
            "score": None,
            "classification_reason": ["project manual default"],
            "evidence_refs": [],
            "factor_snapshot": {},
        }
    else:
        evidence = derive_change_evidence(store, target, _optional_change_evidence(root, target))
        classification = classify_change_level(evidence)

    level = classification["level"]
    provisional = previous.get("provisional_change_level")
    effective = previous.get("effective_change_level")
    history = list(previous.get("escalation_history") or [])
    phase = "TRIAGE" if stage in {"INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY"} else "IMPACT_CONFIRMED"
    if stage in {"INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY"}:
        provisional = provisional or level
        if effective is None:
            effective = provisional
    else:
        provisional = provisional or level
        if effective is None:
            effective = level
        elif LEVELS.index(level) > LEVELS.index(str(effective)):
            history.append({
                "from": effective,
                "to": level,
                "at_stage": stage,
                "detected_at": now(),
                "reason": classification["classification_reason"],
                "evidence_refs": classification["evidence_refs"],
            })
            effective = level
        elif LEVELS.index(level) < LEVELS.index(str(effective)):
            classification["classification_reason"] = list(classification["classification_reason"]) + [
                f"automatic downgrade blocked: observed {level}, retained {effective}"
            ]

    state = {
        "schema_version": 1,
        "target_id": target,
        "policy": policy,
        "phase": phase,
        "provisional_change_level": provisional,
        "effective_change_level": effective,
        "classification_reason": classification["classification_reason"],
        "evidence_refs": classification["evidence_refs"],
        "factor_snapshot": classification.get("factor_snapshot", {}),
        "score": classification.get("score"),
        "escalation_history": history,
        "updated_at": now(),
    }
    path = _change_state_path(root, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def _condition_matches(condition: str | None, context_text: str, level: str) -> bool:
    raw = str(condition or "ALWAYS").strip().upper()
    if raw in {"", "ALWAYS"}:
        return True
    if raw == "HAS_UI":
        return any(k in context_text for k in ["ui", "screen", "jsp", "화면", "web"])
    if raw == "HAS_INTERFACE":
        return any(k in context_text for k in ["interface", "api", "연계", "kafka"])
    if raw == "HAS_BATCH":
        return "batch" in context_text or "배치" in context_text
    if raw == "HAS_DATA_CHANGE":
        return any(k in context_text for k in ["table", "column", "schema", "데이터", "테이블"])
    if raw == "HAS_SECURITY_IMPACT":
        return any(k in context_text for k in ["security", "privacy", "보안", "개인정보", "권한"])
    if raw.startswith("CHANGE_LEVEL_AT_LEAST_"):
        required = raw.rsplit("_", 1)[-1]
        return required in LEVELS and LEVELS.index(level) >= LEVELS.index(required)
    return False


def _render_output_path(row: dict[str, Any], target: str, profile: dict[str, Any], audience_key: str) -> str:
    default_root = str(profile.get("output_root") or {
        "internal": "docs/10_산출물",
        "customer": "docs/20_고객",
        "pm": "docs/00_관리",
    }[audience_key])
    pattern = str(row.get("output_path") or f"{default_root}/{{target}}/{row['id']}.md")
    return pattern.replace("{target}", _safe_target(target)).replace("{artifact_id}", row["id"])


def resolve_artifacts(
    root: Path,
    *,
    project: dict[str, Any],
    target: str,
    stage: str,
    change_level: str,
    store: dict[str, Any] | None = None,
) -> dict[str, Any]:
    store = store or load_store(root)
    distances = _relation_distances(store, target)
    context_text = (_text(store.get("entities", {}).get(target, {})) + " " + " ".join(
        _text(store.get("entities", {}).get(entity_id, {})) for entity_id in distances
    )).lower()
    profile_ids = project_profile_ids(project)
    resolved: dict[str, list[dict[str, Any]]] = {"internal": [], "customer": [], "pm": []}
    profile_paths: dict[str, str] = {}
    for audience_key in ["internal", "customer", "pm"]:
        profile_id = profile_ids[audience_key]
        profile, path = load_profile(root, profile_id)
        profile_paths[audience_key] = path.relative_to(root).as_posix()
        for row in _artifact_rows(profile):
            stages = [str(x).upper() for x in (row.get("sources") or {}).get("stages", [])]
            if stage not in stages:
                continue
            row_levels = [str(x).upper() for x in (row.get("change_levels") or [])]
            if row_levels and change_level not in row_levels:
                continue
            min_level = str(row.get("min_change_level") or "").upper()
            if min_level in LEVELS and LEVELS.index(change_level) < LEVELS.index(min_level):
                continue
            if not _condition_matches(row.get("condition"), context_text, change_level):
                continue
            item = {
                **row,
                "audience": str(row.get("audience") or "").upper(),
                "profile_id": profile_id,
                "profile_path": profile_paths[audience_key],
                "output_path": _render_output_path(row, target, profile, audience_key),
            }
            resolved[audience_key].append(item)

    internal_primary = sorted(
        [x for x in resolved["internal"] if str(x.get("visibility") or "PRIMARY").upper() == "PRIMARY"],
        key=lambda x: (int(x.get("order") or 999), x["id"]),
    )
    primary = internal_primary[0] if internal_primary else None
    return {
        "schema_version": 1,
        "target_id": target,
        "stage": stage,
        "change_level": change_level,
        "profiles": profile_ids,
        "profile_paths": profile_paths,
        "primary_work_artifact": primary,
        "affected_artifacts": resolved,
        "machine_evidence_visibility": str(CONFIG.nested(project, "documents", "machine", "visibility", default="HIDDEN") or "HIDDEN").upper(),
        "stage_preserved": True,
        "projection_creates_business_truth": False,
    }


def projection_freshness(root: Path, canonical_revision: int) -> dict[str, Any]:
    base = root / PROJECTION_RUNTIME_ROOT
    rows: list[dict[str, Any]] = []
    if base.is_dir():
        for path in sorted(base.glob("*.json")):
            try:
                data = load_json(path)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            generated = int(data.get("generated_from_revision") or 0)
            state = "STALE_VIEW" if canonical_revision > generated else "CURRENT"
            rows.append({
                "path": path.relative_to(root).as_posix(),
                "artifact_path": data.get("artifact_path"),
                "audience": data.get("audience"),
                "generated_from_revision": generated,
                "canonical_revision": canonical_revision,
                "freshness": state,
            })
    return {
        "canonical_revision": canonical_revision,
        "views": rows,
        "stale_count": sum(1 for row in rows if row["freshness"] == "STALE_VIEW"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve v1.9 Change Level and Artifact Tailoring.")
    ap.add_argument("command", choices=["validate-profile", "classify", "resolve"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--profile")
    ap.add_argument("--target")
    ap.add_argument("--stage")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "validate-profile":
            if not args.profile:
                raise ValueError("--profile is required")
            profile, path = load_profile(root, args.profile)
            result = {"status": "VALID", "profile_id": profile.get("profile_id"), "path": path.relative_to(root).as_posix()}
        else:
            if not args.target or not args.stage:
                raise ValueError("--target and --stage are required")
            stage = args.stage.upper()
            if stage not in STAGES:
                raise ValueError(f"unsupported stage: {stage}")
            resolved_config = CONFIG.resolve_runtime_config(root)
            project = resolved_config.get("project") or {}
            store = load_store(root)
            level = resolve_change_level(root, args.target, stage, store, project)
            if args.command == "classify":
                result = {"status": "CLASSIFIED", "change_level": level}
            else:
                effective = str(level.get("effective_change_level") or level.get("provisional_change_level") or "L3")
                result = {
                    "status": "RESOLVED",
                    "change_level": level,
                    "tailoring": resolve_artifacts(root, project=project, target=args.target, stage=stage, change_level=effective, store=store),
                }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
