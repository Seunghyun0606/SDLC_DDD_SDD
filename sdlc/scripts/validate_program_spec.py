#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

LEVELS = ["L1", "L2", "L3", "L4", "L5"]


def _triggered(trigger: str, facts: dict) -> bool:
    t = trigger.upper()
    def enum(key: str) -> str: return str(facts.get(key) or "NONE").upper()
    if t == "DATA_MAPPING_IMPACT": return enum("DATA_MAPPING_IMPACT") in {"YES", "LOCAL", "MATERIAL"}
    if t == "DATA_ACCESS_OR_SCHEMA_IMPACT": return enum("DATA_ACCESS_IMPACT") in {"YES", "LOCAL", "MATERIAL"} or enum("SCHEMA_CHANGE") in {"LOCAL", "BREAKING"}
    if t == "COMMON_CODE_IMPACT": return enum("COMMON_CODE_IMPACT") in {"YES", "LOCAL", "MATERIAL"}
    if t == "TRANSACTION_IMPACT": return enum("TRANSACTION_IMPACT") in {"LOCAL", "MATERIAL"}
    if t == "CONCURRENCY_RISK": return enum("CONCURRENCY_RISK") in {"YES", "LOCAL", "MATERIAL", "HIGH"}
    if t == "HAS_INTERFACE": return enum("HAS_INTERFACE") == "YES"
    if t == "ERROR_HANDLING_DELTA": return enum("ERROR_HANDLING_DELTA") in {"YES", "LOCAL", "MATERIAL"}
    if t == "SECURITY_IMPACT": return enum("SECURITY_IMPACT") in {"LOCAL", "MATERIAL"}
    if t == "OBSERVABILITY_IMPACT": return enum("OBSERVABILITY_IMPACT") in {"YES", "LOCAL", "MATERIAL"}
    if t == "NFR_OR_MIGRATION_IMPACT": return enum("NFR_IMPACT") in {"YES", "LOCAL", "MATERIAL"} or enum("MIGRATION_IMPACT") in {"LOCAL", "MATERIAL"}
    if t == "ARCHITECTURE_OR_STANDARD_IMPACT": return enum("ARCHITECTURE_IMPACT") in {"LOCAL", "MATERIAL"} or enum("STANDARD_IMPACT") in {"YES", "LOCAL", "MATERIAL"}
    return False


def required_fields(config: dict, profile: str = "STANDARD", change_level: str = "L3", facts: dict | None = None) -> list[dict]:
    all_fields = {row["id"]: row for row in config["required_fields"]}
    # Backward compatibility for old config shapes.
    if "core_required_field_ids" not in config:
        profile_cfg = (config.get("profiles") or {}).get(profile.upper())
        ids = profile_cfg.get("required_field_ids", []) if profile_cfg else list(all_fields)
        return [all_fields[x] for x in ids if x in all_fields]
    if profile.upper() in {"LEGACY_FULL_17", "LEGACY", "STAGE_ORIENTED_FULL"}:
        ids = (config.get("legacy_compatibility") or {}).get("required_field_ids", [])
        return [all_fields[x] for x in ids if x in all_fields]
    ids = list(config.get("core_required_field_ids") or [])
    typed = facts or {}
    for row in config.get("conditional_fields") or []:
        if _triggered(str(row.get("trigger") or ""), typed):
            ids.append(str(row.get("field_id")))
    seen: set[str] = set()
    return [all_fields[x] for x in ids if x in all_fields and not (x in seen or seen.add(x))]


def validate_text(text: str, config: dict, profile: str = "STANDARD", change_level: str = "L3", facts: dict | None = None) -> list[str]:
    errors: list[str] = []
    for field in required_fields(config, profile, change_level, facts):
        markers = [field["marker"]] + list(field.get("legacy_markers") or [])
        if not any(marker in text for marker in markers):
            errors.append(f"MISSING_READINESS_ITEM:{field['id']}:{field['label']}")

    ready = any(x in text for x in ["구현 준비 상태: READY", "구현 준비 판정: READY", "Implementation Readiness: READY", "Readiness Verdict: READY"])
    rules = config["rules"]
    if ready and rules.get("simulated_source_cannot_be_ready") and "SIMULATED_REFERENCE_ARCHITECTURE" in text:
        errors.append("READY_WITH_SIMULATED_SOURCE")
    if ready and rules.get("open_real_source_cannot_be_ready") and "OPEN_REAL_SOURCE" in text:
        errors.append("READY_WITH_OPEN_REAL_SOURCE")
    zero_open = any(x in text for x in ["남은 구현 OPEN 수: 0", "남은 구현 OPEN 수: `0`", "미확정 항목 수: 0", "미확정 항목 수: `0`", "OPEN Count: 0", "OPEN Count: `0`"])
    if ready and rules.get("ready_requires_zero_open") and not zero_open:
        errors.append("READY_WITH_NONZERO_OR_UNKNOWN_OPEN")
    threshold = str(rules.get("functional_design_reference_required_from_change_level") or "L1").upper()
    level = change_level.upper()
    if ready and threshold in LEVELS and level in LEVELS and LEVELS.index(level) >= LEVELS.index(threshold):
        if not any(x in text for x in ["기능 설계 문서/버전:", "Functional Design Ref:"]):
            errors.append("READY_WITHOUT_FUNCTIONAL_DESIGN_REFERENCE")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--config", default="sdlc/config/program-spec-readiness.json")
    parser.add_argument("--profile", default="STANDARD")
    parser.add_argument("--change-level", default="L3", choices=LEVELS)
    parser.add_argument("--facts", help="Typed facts JSON; only triggered risk fields become required")
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8")) if args.facts else {}
    if isinstance(facts.get("facts"), dict): facts = facts["facts"]
    failed = False
    for file in args.files:
        p = Path(file); errors = validate_text(p.read_text(encoding="utf-8"), config, args.profile, args.change_level, facts)
        if errors:
            failed = True; print(f"FAIL {p} [{args.profile}/{args.change_level}]: " + ", ".join(errors))
        else:
            print(f"PASS {p} [{args.profile}/{args.change_level}]")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
