#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate_text(text: str, config: dict) -> list[str]:
    errors = []
    for field in config["required_fields"]:
        if field["marker"] not in text:
            errors.append(f"MISSING_SECTION:{field['id']}:{field['marker']}")
    ready = "Implementation Readiness: READY" in text or "Readiness Verdict: READY" in text
    if ready and config["rules"].get("simulated_source_cannot_be_ready") and "SIMULATED_REFERENCE_ARCHITECTURE" in text:
        errors.append("READY_WITH_SIMULATED_SOURCE")
    if ready and config["rules"].get("open_real_source_cannot_be_ready") and "OPEN_REAL_SOURCE" in text:
        errors.append("READY_WITH_OPEN_REAL_SOURCE")
    if ready and config["rules"].get("ready_requires_zero_open") and ("OPEN Count: 0" not in text and "OPEN Count: `0`" not in text):
        errors.append("READY_WITH_NONZERO_OR_UNKNOWN_OPEN")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--config", default="sdlc/config/program-spec-readiness.json")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    failed = False
    for file in args.files:
        p = Path(file)
        errors = validate_text(p.read_text(encoding="utf-8"), config)
        if errors:
            failed = True
            print(f"FAIL {p}: " + ", ".join(errors))
        else:
            print(f"PASS {p}")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
