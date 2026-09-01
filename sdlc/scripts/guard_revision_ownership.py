#!/usr/bin/env python3
"""Pre-write guard for revision and multi-agent file ownership."""
from __future__ import annotations
import argparse, fnmatch
from pathlib import Path
from typing import Any
import yaml

def load(path:Path)->dict[str,Any]: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def matches(path:str,patterns:list[str])->bool: return any(fnmatch.fnmatch(path,p) for p in patterns)

def guard(doc:dict[str,Any])->dict[str,Any]:
    ctx=(doc or {}).get("change_execution") or {}
    ownership=ctx.get("ownership") or {}
    requested=list(ownership.get("requested_paths") or [])
    owned=list(ownership.get("owned_paths") or [])
    shared=list(ownership.get("shared_paths") or [])
    proof=ownership.get("coordination_proof_ref")
    blockers=[]
    expected=ctx.get("expected_revision"); current=ctx.get("current_revision")
    if not expected or not current or expected != current:
        blockers.append({"code":"REVISION_MISMATCH","expected_revision":expected,"current_revision":current})
    if not ctx.get("agent_branch") or not ctx.get("parent_change_branch"):
        blockers.append({"code":"BRANCH_CONTEXT_REQUIRED"})
    for path in requested:
        if matches(path,owned):
            continue
        if matches(path,shared):
            if not proof:
                blockers.append({"code":"SHARED_PATH_COORDINATION_REQUIRED","path":path})
            continue
        blockers.append({"code":"PATH_NOT_OWNED","path":path})
    agent=ctx.get("agent_id")
    for claim in ownership.get("active_claims") or []:
        if claim.get("agent_id") == agent: continue
        for path in requested:
            if matches(path,list(claim.get("paths") or [])):
                blockers.append({"code":"ACTIVE_OWNERSHIP_CONFLICT","path":path,"conflicting_agent_id":claim.get("agent_id")})
    decision="ALLOW" if not blockers else "DENY"
    return {"schema_version":1,"artifact_type":"REVISION_OWNERSHIP_GUARD_RESULT","revision_ownership_guard":{"change_id":ctx.get("change_id"),"agent_id":agent,"decision":decision,"guard_proof_ref":f"GUARD:{ctx.get('change_id')}:{current}" if decision=="ALLOW" else None,"requested_paths":requested,"blockers":blockers,"truth_guards":{"revision_mismatch_must_not_auto_overwrite":True,"shared_path_requires_coordination":True}}}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("context",type=Path); p.add_argument("-o","--output",type=Path); a=p.parse_args(); result=guard(load(a.context)); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0 if result["revision_ownership_guard"]["decision"]=="ALLOW" else 1
if __name__=="__main__":raise SystemExit(main())
