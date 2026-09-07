#!/usr/bin/env python3
"""Artifact Tailoring + typed Change Level runtime.

Stage remains an internal compatibility taxonomy. Change Level classification is delegated to the
typed execution runtime; free text may create candidate hints but never directly raises a level.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = _load("tailoring_config_v19", "runtime_config_v19.py")
EXEC = _load("tailoring_change_execution", "change_execution_runtime.py")
STAGES = ["INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT", "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION"]
LEVELS = ["L1", "L2", "L3", "L4", "L5"]
LEVEL_NAMES = {"L1": "MICRO", "L2": "LOCAL", "L3": "FEATURE", "L4": "PROCESS", "L5": "ARCH"}
AUDIENCES = {"MACHINE", "INTERNAL_IT", "PM_REVIEW", "CUSTOMER"}
# Keep direct Tailoring Runtime use aligned with the canonical project-config resolver.
# `internal` remains the compatibility audience key, but its default is the current Engineering profile.
DEFAULT_PROFILES = {
    "internal": CONFIG.DEFAULT_ENGINEERING_PROFILE,
    "customer": CONFIG.DEFAULT_CUSTOMER_PROFILE,
    "pm": CONFIG.DEFAULT_PM_PROFILE,
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
    data.setdefault("revision", 0); data.setdefault("entities", {}); data.setdefault("relations", [])
    return data


def _safe_target(target: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", target).strip("_") or "TARGET"


def _profile_candidates(root: Path, profile_id: str) -> list[Path]:
    names = [profile_id, f"internal-{profile_id}", f"customer-{profile_id}", f"pm-{profile_id}"]
    out: list[Path] = []
    for base in PROFILE_ROOTS:
        for name in names:
            for suffix in [".yaml", ".yml", ".json"]:
                path = root / base / f"{name}{suffix}"
                if path not in out: out.append(path)
    return out


def _artifact_rows(profile: dict[str, Any]) -> list[dict[str, Any]]:
    raw = profile.get("artifacts") or {}
    if not isinstance(raw, dict): raise ValueError("tailoring artifacts must be a mapping keyed by artifact id")
    rows: list[dict[str, Any]] = []
    for artifact_id, value in raw.items():
        if not isinstance(value, dict): raise ValueError(f"artifact {artifact_id} must be a mapping")
        row = dict(value); row["id"] = str(artifact_id); rows.append(row)
    return rows


def validate_profile(profile: dict[str, Any], *, root: Path | None = None, source_path: Path | None = None) -> None:
    if int(profile.get("schema_version", 0) or 0) != 1: raise ValueError(f"tailoring profile schema_version must be 1: {source_path or '<memory>'}")
    if not str(profile.get("profile_id") or "").strip(): raise ValueError("tailoring profile_id is required")
    seen: set[str] = set()
    for row in _artifact_rows(profile):
        artifact_id = row["id"]
        if artifact_id in seen: raise ValueError(f"duplicate artifact id: {artifact_id}")
        seen.add(artifact_id)
        audience = str(row.get("audience") or "").upper()
        if audience not in AUDIENCES: raise ValueError(f"artifact {artifact_id} has unsupported audience: {audience}")
        template = str(row.get("template") or "").strip()
        if not template: raise ValueError(f"artifact {artifact_id} template is required")
        sources = row.get("sources") or {}
        if not isinstance(sources, dict): raise ValueError(f"artifact {artifact_id} sources must be a mapping")
        stages = sources.get("stages") or []
        if not isinstance(stages, list) or not stages: raise ValueError(f"artifact {artifact_id} requires sources.stages")
        unknown = [str(x) for x in stages if str(x).upper() not in STAGES]
        if unknown: raise ValueError(f"artifact {artifact_id} has unknown stage(s): {', '.join(unknown)}")
        if root is not None and not (root / template).is_file(): raise ValueError(f"artifact {artifact_id} template not found: {template}")


def load_profile(root: Path, profile_id: str) -> tuple[dict[str, Any], Path]:
    for path in _profile_candidates(root, profile_id):
        if path.is_file():
            profile = CONFIG.load_config(path); validate_profile(profile, root=root, source_path=path); return profile, path
    raise ValueError(f"tailoring profile not found: {profile_id}")


def project_profile_ids(project: dict[str, Any]) -> dict[str, str]:
    return {audience: str(CONFIG.nested(project, "documents", audience, "profile", default=default) or default) for audience, default in DEFAULT_PROFILES.items()}


def _relation_distances(store: dict[str, Any], target: str, max_hops: int = 4) -> dict[str, int]:
    return EXEC._distances(store, target, max_hops)


def _text(value: Any) -> str:
    return EXEC._text(value)


def derive_change_evidence(store: dict[str, Any], target: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return EXEC.derive_typed_facts(store, target, extra)


def _legacy_evidence_to_typed(evidence: dict[str, Any]) -> dict[str, Any]:
    if isinstance(evidence.get("facts"), dict): return evidence
    facts = dict(EXEC.FACT_DEFAULTS)
    count = int(evidence.get("changed_component_count") or 0); facts["CHANGED_COMPONENT_COUNT"] = count
    if evidence.get("cross_domain"): facts["CROSS_DOMAIN_COUNT"] = 2
    if "cross_domain_count" in evidence: facts["CROSS_DOMAIN_COUNT"] = int(evidence.get("cross_domain_count") or 0)
    facts["BUSINESS_RULE_IMPACT"] = "MATERIAL" if evidence.get("business_rule_impact") else "NONE"
    facts["HAS_INTERFACE"] = "YES" if evidence.get("external_interface") else "NO"
    facts["HAS_BATCH"] = "YES" if evidence.get("batch") else "NO"
    facts["SCHEMA_CHANGE"] = "LOCAL" if evidence.get("data_or_schema_change") else "NONE"
    facts["TRANSACTION_IMPACT"] = "LOCAL" if evidence.get("transaction") else "NONE"
    facts["SECURITY_IMPACT"] = "MATERIAL" if evidence.get("security_or_privacy") else "NONE"
    facts["ARCHITECTURE_IMPACT"] = "MATERIAL" if evidence.get("architecture_change") else "NONE"
    facts["OPERATIONAL_RISK"] = str(evidence.get("operational_risk") or "NORMAL").upper()
    facts["IMPACT_COVERAGE"] = "PARTIAL" if evidence.get("brownfield_impact_coverage_uncertainty") else "COMPLETE"
    return {"facts": facts, "evidence_refs": list(evidence.get("evidence_refs") or []), "candidate_hints": []}


def classify_change_level(evidence: dict[str, Any]) -> dict[str, Any]:
    result = EXEC.classify_typed_facts(_legacy_evidence_to_typed(evidence))
    result["name"] = LEVEL_NAMES[result["level"]]
    result["factor_snapshot"] = result.get("typed_facts", {})
    return result


def _change_state_path(root: Path, target: str) -> Path:
    return root / CHANGE_RUNTIME_ROOT / f"{_safe_target(target)}.json"


def load_change_state(root: Path, target: str) -> dict[str, Any]:
    path = _change_state_path(root, target); return load_json(path) if path.is_file() else {}


def resolve_change_level(root: Path, target: str, stage: str, store: dict[str, Any], project: dict[str, Any]) -> dict[str, Any]:
    phase = "TRIAGE" if stage in {"INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY"} else "IMPACT_CONFIRMED"
    return EXEC.resolve_change(root, target, store, project, phase=phase)


def _condition_matches(condition: str | None, facts: dict[str, Any], context_text: str, level: str) -> bool:
    raw = str(condition or "ALWAYS").strip().upper()
    if raw in {"", "ALWAYS"}: return True
    if raw == "HAS_UI": return any(k in context_text for k in ["ui", "screen", "jsp", "화면", "web"])
    if raw == "HAS_INTERFACE": return str(facts.get("HAS_INTERFACE")).upper() == "YES"
    if raw == "HAS_BATCH": return str(facts.get("HAS_BATCH")).upper() == "YES"
    if raw == "HAS_DATA_CHANGE": return str(facts.get("SCHEMA_CHANGE")).upper() in {"LOCAL", "BREAKING"}
    if raw == "HAS_SECURITY_IMPACT": return str(facts.get("SECURITY_IMPACT")).upper() in {"LOCAL", "MATERIAL"}
    if raw.startswith("CHANGE_LEVEL_AT_LEAST_"):
        required = raw.rsplit("_", 1)[-1]; return required in LEVELS and LEVELS.index(level) >= LEVELS.index(required)
    return False


def _render_output_path(row: dict[str, Any], target: str, profile: dict[str, Any], audience_key: str) -> str:
    default_root = str(profile.get("output_root") or {"internal": "docs/10_산출물", "customer": "docs/20_고객", "pm": "docs/00_관리"}[audience_key])
    pattern = str(row.get("output_path") or f"{default_root}/{{target}}/{row['id']}.md")
    return pattern.replace("{target}", _safe_target(target)).replace("{artifact_id}", row["id"])


def resolve_artifacts(root: Path, *, project: dict[str, Any], target: str, stage: str, change_level: str, store: dict[str, Any] | None = None) -> dict[str, Any]:
    store = store or load_store(root)
    distances = _relation_distances(store, target)
    context_text = (_text((store.get("entities") or {}).get(target, {})) + " " + " ".join(_text((store.get("entities") or {}).get(entity_id, {})) for entity_id in distances)).lower()
    typed = derive_change_evidence(store, target, {}).get("facts") or {}
    profile_ids = project_profile_ids(project)
    resolved: dict[str, list[dict[str, Any]]] = {"internal": [], "customer": [], "pm": []}; profile_paths: dict[str, str] = {}
    for audience_key in ["internal", "customer", "pm"]:
        profile_id = profile_ids[audience_key]; profile, path = load_profile(root, profile_id); profile_paths[audience_key] = path.relative_to(root).as_posix()
        for row in _artifact_rows(profile):
            stages = [str(x).upper() for x in (row.get("sources") or {}).get("stages", [])]
            if stage not in stages: continue
            row_levels = [str(x).upper() for x in (row.get("change_levels") or [])]
            if row_levels and change_level not in row_levels: continue
            min_level = str(row.get("min_change_level") or "").upper()
            if min_level in LEVELS and LEVELS.index(change_level) < LEVELS.index(min_level): continue
            if not _condition_matches(row.get("condition"), typed, context_text, change_level): continue
            resolved[audience_key].append({**row, "audience": str(row.get("audience") or "").upper(), "profile_id": profile_id, "profile_path": profile_paths[audience_key], "output_path": _render_output_path(row, target, profile, audience_key)})
    internal_primary = sorted([x for x in resolved["internal"] if str(x.get("visibility") or "PRIMARY").upper() == "PRIMARY"], key=lambda x: (int(x.get("order") or 999), x["id"]))
    return {"schema_version": 2, "target_id": target, "stage": stage, "change_level": change_level, "profiles": profile_ids, "profile_paths": profile_paths, "primary_work_artifact": internal_primary[0] if internal_primary else None, "affected_artifacts": resolved, "machine_evidence_visibility": str(CONFIG.nested(project, "documents", "machine", "visibility", default="HIDDEN") or "HIDDEN").upper(), "stage_preserved": True, "projection_creates_business_truth": False}


def projection_freshness(root: Path, canonical_revision: int) -> dict[str, Any]:
    base = root / PROJECTION_RUNTIME_ROOT; rows: list[dict[str, Any]] = []
    if base.is_dir():
        for path in sorted(base.glob("*.json")):
            try: data = load_json(path)
            except (OSError, json.JSONDecodeError, ValueError): continue
            generated = int(data.get("generated_from_revision") or 0)
            lifecycle = str(data.get("lifecycle") or "CURRENT").upper()
            if canonical_revision > generated: state = "STALE_VIEW"
            elif lifecycle == "PENDING_REVIEW": state = "PENDING_REVIEW"
            else: state = "CURRENT"
            rows.append({"path": path.relative_to(root).as_posix(), "target_id": data.get("target_id"), "artifact_id": data.get("artifact_id"), "artifact_path": data.get("artifact_path"), "audience": data.get("audience"), "generated_from_revision": generated, "canonical_revision": canonical_revision, "freshness": state, "lifecycle": lifecycle})
    return {"canonical_revision": canonical_revision, "views": rows, "stale_count": sum(1 for x in rows if x["freshness"] == "STALE_VIEW"), "pending_review_count": sum(1 for x in rows if x["freshness"] == "PENDING_REVIEW"), "current_count": sum(1 for x in rows if x["freshness"] == "CURRENT")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve typed Change Level and Artifact Tailoring.")
    ap.add_argument("command", choices=["validate-profile", "classify", "resolve"]); ap.add_argument("--root", default="."); ap.add_argument("--profile"); ap.add_argument("--target"); ap.add_argument("--stage")
    args = ap.parse_args(argv); root = Path(args.root).resolve()
    try:
        if args.command == "validate-profile":
            if not args.profile: raise ValueError("--profile is required")
            profile, path = load_profile(root, args.profile); result = {"status": "VALID", "profile_id": profile.get("profile_id"), "path": path.relative_to(root).as_posix()}
        else:
            if not args.target or not args.stage: raise ValueError("--target and --stage are required")
            stage = args.stage.upper()
            if stage not in STAGES: raise ValueError(f"unsupported stage: {stage}")
            project = CONFIG.resolve_runtime_config(root).get("project") or {}; store = load_store(root); level = resolve_change_level(root, args.target, stage, store, project)
            if args.command == "classify": result = {"status": "CLASSIFIED", "change_level": level}
            else:
                effective = str(level.get("effective_change_level") or level.get("provisional_change_level") or "L3")
                result = {"status": "RESOLVED", "change_level": level, "execution_policy": EXEC.resolve_execution_plan(root, level), "tailoring": resolve_artifacts(root, project=project, target=args.target, stage=stage, change_level=effective, store=store)}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
