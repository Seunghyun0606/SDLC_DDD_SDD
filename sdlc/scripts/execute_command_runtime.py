#!/usr/bin/env python3
"""Execute /work, /change, /check through capability routing and P0.8 invocation."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml
from route_provider_command import build_plan
from invoke_provider_runtime import invoke_request

def load(p:Path): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def _scopes(item:dict[str,Any]):
    scopes=item.get("action_scopes") or item.get("action_scope") or []
    return [scopes] if isinstance(scopes,str) else list(scopes)

def execute(registry:dict[str,Any], context:dict[str,Any]):
    plan, errors=build_plan(registry,context)
    if errors:
        return {"command_runtime_result":{"command_id":context.get("command_id"),"state":"INVALID","plan":plan,"errors":errors,"invocations":[],"open_items":[]}}

    runtime=plan.get("runtime_plan") or {}
    open_items=list(runtime.get("open_items") or [])
    blocking_open=[x for x in open_items if x.get("blocks_action") is True]
    human_actions=list(context.get("human_actions") or [])
    blocking_human=[x for x in human_actions if x.get("blocks_action",True)]
    resolved=list(runtime.get("resolved_providers") or [])
    invocations=[]
    skipped=[]
    capability_inputs=context.get("capability_inputs") or {}
    write_caps=set(context.get("write_capabilities") or [])
    proofs=context.get("write_proofs") or {}
    adapter_configs=context.get("adapter_configs") or {}

    blocked_caps=set()
    global_block=False
    for item in blocking_open:
        scopes=_scopes(item)
        if "*" in scopes: global_block=True
        blocked_caps.update(x for x in scopes if x!="*")
    for action in blocking_human:
        cap=action.get("capability")
        scopes=_scopes(action)
        if action.get("global_block") is True or "*" in scopes: global_block=True
        if cap: blocked_caps.add(cap)
        blocked_caps.update(x for x in scopes if x!="*")

    external=[x for x in resolved if x.get("provider_type")!="COMMAND_ROUTER"]
    for idx,item in enumerate(external,1):
        cap=item.get("capability")
        if global_block or cap in blocked_caps:
            skipped.append({"capability":cap,"reason":"ACTION_GUARDED"})
            continue
        write=cap in write_caps; proof=proofs.get(cap) or {}
        req={"provider_request":{
            "request_id":f"{context.get('command_id','CMD')}-REQ-{idx:02d}","provider_type":item.get("provider_type"),"operation":cap,
            "project_context":context.get("project_context") or {},"target":context.get("target") or {},"inputs":[],"write_intent":write,
            "expected_revision":proof.get("expected_revision"),"idempotency_key":proof.get("idempotency_key"),"permission_proof_ref":proof.get("permission_proof_ref"),
            "constraints":{"do_not_invent_missing_result":True},"extensions":capability_inputs.get(cap) or {}}}
        journal,response=invoke_request(registry,req,adapter_configs)
        invocations.append({"capability":cap,"request":req,"journal":journal,"response":response})

    states=[x["journal"]["invocation_journal"]["state"] for x in invocations]
    if "UNKNOWN_AFTER_WRITE" in states:
        state="RECOVERY_REQUIRED"
    elif any(s in {"BLOCKED","FAILED"} for s in states):
        state="ACTION_REQUIRED"
    elif blocking_open or blocking_human:
        state="ACTION_REQUIRED"
    elif "PARTIAL" in states or open_items or human_actions:
        state="PARTIAL"
    else:
        state="COMPLETE"

    return {"command_runtime_result":{
        "command_id":context.get("command_id"),"command":context.get("command"),"state":state,
        "plan":plan,"errors":[],"invocations":invocations,"skipped_invocations":skipped,
        "open_items":open_items,"human_actions":human_actions,
        "blocked_action_open_ids":[x.get("open_id") for x in blocking_open if x.get("open_id")],
        "partial_progress_performed":bool(invocations) and bool(blocking_open or blocking_human),
    }}

def main():
    p=argparse.ArgumentParser(); p.add_argument("registry",type=Path); p.add_argument("context",type=Path); p.add_argument("-o","--output",type=Path); a=p.parse_args()
    result=execute(load(a.registry),load(a.context)); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0 if result["command_runtime_result"]["state"] in {"COMPLETE","PARTIAL"} else 1
if __name__=="__main__": raise SystemExit(main())
