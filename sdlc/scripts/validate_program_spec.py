#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def required_fields(config: dict, profile: str) -> list[dict]:
    all_fields = {row["id"]: row for row in config["required_fields"]}
    profile = profile.upper()
    profile_cfg = (config.get("profiles") or {}).get(profile)
    if not profile_cfg:
        return list(config["required_fields"])
    return [all_fields[field_id] for field_id in profile_cfg.get("required_field_ids", []) if field_id in all_fields]


def validate_text(text: str, config: dict, profile: str = "STANDARD") -> list[str]:
    errors = []
    for field in required_fields(config, profile):
        if field["marker"] not in text:
            errors.append(f"MISSING_READINESS_ITEM:{field['id']}:{field['label']}")

    ready = any(x in text for x in [
        "구현 준비 상태: READY", "구현 준비 판정: READY",
        "Implementation Readiness: READY", "Readiness Verdict: READY",
    ])
    rules = config["rules"]
    if ready and rules.get("simulated_source_cannot_be_ready") and "SIMULATED_REFERENCE_ARCHITECTURE" in text:
        errors.append("READY_WITH_SIMULATED_SOURCE")
    if ready and rules.get("open_real_source_cannot_be_ready") and "OPEN_REAL_SOURCE" in text:
        errors.append("READY_WITH_OPEN_REAL_SOURCE")
    zero_open = any(x in text for x in [
        "남은 구현 OPEN 수: 0", "남은 구현 OPEN 수: `0`", "미확정 항목 수: 0",
        "미확정 항목 수: `0`", "OPEN Count: 0", "OPEN Count: `0`",
    ])
    if ready and rules.get("ready_requires_zero_open") and not zero_open:
        errors.append("READY_WITH_NONZERO_OR_UNKNOWN_OPEN")
    if ready and rules.get("ready_requires_functional_design_reference"):
        if not any(x in text for x in ["기능 설계 문서/버전:", "Functional Design Ref:"]):
            errors.append("READY_WITHOUT_FUNCTIONAL_DESIGN_REFERENCE")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--config", default="sdlc/config/program-spec-readiness.json")
    parser.add_argument("--profile", default="STANDARD", choices=["FAST", "STANDARD", "FULL"])
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    failed = False
    for file in args.files:
        p = Path(file)
        errors = validate_text(p.read_text(encoding="utf-8"), config, args.profile)
        if errors:
            failed = True
            print(f"FAIL {p} [{args.profile}]: " + ", ".join(errors))
        else:
            print(f"PASS {p} [{args.profile}]")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
