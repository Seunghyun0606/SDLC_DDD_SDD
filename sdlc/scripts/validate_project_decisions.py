#!/usr/bin/env python3
from __future__ import annotations
import argparse,sys
from pathlib import Path
import yaml
from build_project_decision_registry import validate

def load(p:Path): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
def main():
    p=argparse.ArgumentParser(); p.add_argument("instance",type=Path); p.add_argument("--config",type=Path,default=Path("sdlc/config/project-decisions.yaml")); a=p.parse_args()
    errors=validate(load(a.instance),load(a.config))
    if errors: print("\n".join(errors),file=sys.stderr); return 1
    print(f"OK: project decisions valid: {a.instance}"); return 0
if __name__=="__main__": raise SystemExit(main())
