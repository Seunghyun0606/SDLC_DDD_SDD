#!/usr/bin/env python3
"""Domain-neutral E2E status aggregator for stage execution ledgers."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml

VALID_STATES={"NOT_STARTED","READY","COMPLETE","PARTIAL","ACTION_REQUIRED","BLOCKED","FAILED"}

def load(path:Path)->dict[str,Any]: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def build(doc:dict[str,Any])->dict[str,Any]:
    ledger=(doc or {}).get("e2e_execution_ledger") or {}
    stages=list(ledger.get("stages") or [])
    errors=[]
    for i,stage in enumerate(stages):
        if stage.get("state") not in VALID_STATES: errors.append(f"stage[{i}] invalid state: {stage.get('state')}")
        if not stage.get("stage"): errors.append(f"stage[{i}] stage required")
    if errors: raise ValueError("; ".join(errors))
    blockers=list(ledger.get("blockers") or [])
    release_blockers=[b for b in blockers if b.get("blocks_release") is True]
    required=[s for s in stages if s.get("required_for_release") is True]
    failed=any(s.get("state")=="FAILED" for s in stages)
    required_incomplete=[s for s in required if s.get("state")!="COMPLETE"]
    verification=ledger.get("verification") or {}
    production_verified=verification.get("production_verified") is True
    verified_pass=verification.get("state")=="VERIFIED_PASS"
    if failed: overall="FAILED"
    elif release_blockers or required_incomplete: overall="ACTION_REQUIRED"
    elif any(s.get("state") in {"PARTIAL","ACTION_REQUIRED","BLOCKED"} for s in stages): overall="PARTIAL"
    elif production_verified and verified_pass: overall="READY_FOR_RELEASE"
    else: overall="PARTIAL"
    return {"schema_version":1,"artifact_type":"E2E_CHECK_STATUS","e2e_check_status":{
        "subject":ledger.get("subject") or {},"overall":{"state":overall,"release_ready":overall=="READY_FOR_RELEASE","production_verified":production_verified},
        "stages":stages,"blockers":blockers,"required_incomplete_stages":[s.get("stage") for s in required_incomplete],
        "next_actions":[b.get("action") for b in blockers if b.get("action")][:5],
        "truth_guards":{"production_verification_required_for_release":True,"open_or_partial_is_not_success":True,"source_behavior_is_not_business_truth":True}}}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("ledger",type=Path); p.add_argument("-o","--output",type=Path); a=p.parse_args(); result=build(load(a.ledger)); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0
if __name__=="__main__":raise SystemExit(main())
