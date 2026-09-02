#!/usr/bin/env python3
"""Pre-write guard for real Git revision, branch and multi-agent ownership claims."""
from __future__ import annotations
import argparse, fnmatch, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml


def load(path:Path)->dict[str,Any]: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
def matches(path:str,patterns:list[str])->bool: return any(fnmatch.fnmatch(path,p) for p in patterns)

def _git(project_root: Path, *args: str) -> str:
    cp=subprocess.run(["git","-C",str(project_root),*args],shell=False,capture_output=True,text=True,check=True)
    return cp.stdout.strip()

def _claim_active(claim:dict[str,Any])->bool:
    if claim.get("status")!="ACTIVE": return False
    raw=claim.get("expires_at")
    if not raw: return True
    try: expires=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
    except ValueError: return False
    return expires>datetime.now(timezone.utc)

def guard(doc:dict[str,Any])->dict[str,Any]:
    ctx=(doc or {}).get("change_execution") or {}
    ownership=ctx.get("ownership") or {}
    requested=list(ownership.get("requested_paths") or [])
    owned=list(ownership.get("owned_paths") or [])
    shared=list(ownership.get("shared_paths") or [])
    proof=ownership.get("coordination_proof_ref")
    blockers=[]
    expected=ctx.get("expected_revision")
    current=ctx.get("current_revision")
    actual_branch=None
    project_root_raw=ctx.get("project_root")
    if project_root_raw:
        root=Path(str(project_root_raw)).expanduser().resolve()
        try:
            current=_git(root,"rev-parse","HEAD")
            actual_branch=_git(root,"rev-parse","--abbrev-ref","HEAD")
        except (subprocess.CalledProcessError,OSError) as exc:
            blockers.append({"code":"GIT_CONTEXT_UNAVAILABLE","message":str(exc)})
    if not expected or not current or expected != current:
        blockers.append({"code":"REVISION_MISMATCH","expected_revision":expected,"current_revision":current})
    if not ctx.get("agent_branch") or not ctx.get("parent_change_branch"):
        blockers.append({"code":"BRANCH_CONTEXT_REQUIRED"})
    if actual_branch is not None and ctx.get("agent_branch") and actual_branch != ctx.get("agent_branch"):
        blockers.append({"code":"AGENT_BRANCH_MISMATCH","expected_branch":ctx.get("agent_branch"),"current_branch":actual_branch})
    for path in requested:
        if matches(path,owned):
            continue
        if matches(path,shared):
            if not proof:
                blockers.append({"code":"SHARED_PATH_COORDINATION_REQUIRED","path":path})
            continue
        blockers.append({"code":"PATH_NOT_OWNED","path":path})
    agent=ctx.get("agent_id")
    inline_claims=list(ownership.get("active_claims") or [])
    for claim in inline_claims:
        if claim.get("agent_id") == agent: continue
        for path in requested:
            if matches(path,list(claim.get("paths") or [])):
                blockers.append({"code":"ACTIVE_OWNERSHIP_CONFLICT","path":path,"conflicting_agent_id":claim.get("agent_id")})

    active_claim_id=ownership.get("active_claim_id")
    claim_store=ownership.get("claim_store")
    if active_claim_id:
        if not claim_store and project_root_raw:
            claim_store=str(Path(str(project_root_raw)).expanduser().resolve()/".ai-sdlc"/"claims"/"source-claims.yaml")
        if not claim_store or not Path(str(claim_store)).is_file():
            blockers.append({"code":"ACTIVE_CLAIM_STORE_REQUIRED","claim_id":active_claim_id})
        else:
            store=load(Path(str(claim_store)))
            matching=[c for c in store.get("claims") or [] if c.get("claim_id")==active_claim_id and _claim_active(c)]
            if not matching:
                blockers.append({"code":"ACTIVE_CLAIM_REQUIRED","claim_id":active_claim_id})
            else:
                claim=matching[0]
                if claim.get("agent_id")!=agent:
                    blockers.append({"code":"CLAIM_OWNER_MISMATCH","claim_id":active_claim_id,"claim_agent_id":claim.get("agent_id")})
                for path in requested:
                    if not matches(path,list(claim.get("paths") or [])):
                        blockers.append({"code":"CLAIM_DOES_NOT_COVER_PATH","claim_id":active_claim_id,"path":path})
                if expected and claim.get("expected_revision") and claim.get("expected_revision")!=expected:
                    blockers.append({"code":"CLAIM_REVISION_MISMATCH","claim_id":active_claim_id,"claim_revision":claim.get("expected_revision"),"expected_revision":expected})
    elif ownership.get("require_atomic_claim") is True:
        blockers.append({"code":"ATOMIC_CLAIM_REQUIRED"})

    decision="ALLOW" if not blockers else "DENY"
    guard_ref=f"GUARD:{ctx.get('change_id')}:{current}:{active_claim_id or 'NOCLAIM'}" if decision=="ALLOW" else None
    return {"schema_version":1,"artifact_type":"REVISION_OWNERSHIP_GUARD_RESULT","revision_ownership_guard":{
        "change_id":ctx.get("change_id"),"agent_id":agent,"decision":decision,"guard_proof_ref":guard_ref,
        "expected_revision":expected,"current_revision":current,"current_branch":actual_branch or ctx.get("agent_branch"),
        "active_claim_id":active_claim_id,"requested_paths":requested,"blockers":blockers,
        "truth_guards":{"revision_mismatch_must_not_auto_overwrite":True,"shared_path_requires_coordination":True,
                        "real_git_revision_preferred":True,"atomic_claim_required_when_configured":True}}}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("context",type=Path); p.add_argument("-o","--output",type=Path); a=p.parse_args(); result=guard(load(a.context)); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0 if result["revision_ownership_guard"]["decision"]=="ALLOW" else 1
if __name__=="__main__":raise SystemExit(main())
