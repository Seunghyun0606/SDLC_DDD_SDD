#!/usr/bin/env python3
"""Build a deterministic provider runtime plan without invoking providers."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any
import yaml

COMMAND_CAPABILITY={"/work":"command.route.work","/change":"command.route.change","/check":"command.route.check"}
USABLE_PROVIDER_STATES={"AVAILABLE","DEGRADED"}

def load(path:Path)->dict[str,Any]: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def select(registry:dict[str,Any], capability:str, write_intent:bool=False):
    declared=[]; usable=[]
    for p in ((registry.get("registry") or {}).get("providers") or []):
        if p.get("enabled") is not True or capability not in (p.get("capabilities") or []): continue
        declared.append(p)
        if p.get("provider_state") not in USABLE_PROVIDER_STATES: continue
        if write_intent and p.get("mode")!="READ_WRITE": continue
        usable.append(p)
    if not usable:
        return None, "PROVIDER_UNAVAILABLE" if declared else "MISSING_CAPABILITY"
    ranked=sorted(usable,key=lambda p:(int(p.get("priority",100)),str(p.get("provider_id"))))
    if len(ranked)>1 and int(ranked[0].get("priority",100))==int(ranked[1].get("priority",100)):
        return None,"AMBIGUOUS_PROVIDER"
    return ranked[0],None

def build_plan(registry:dict[str,Any], context:dict[str,Any]):
    errors=[]; command=context.get("command")
    if command not in COMMAND_CAPABILITY: return {},["ROUTE-001: command must be /work, /change, or /check"]

    router_cap=COMMAND_CAPABILITY[command]
    requested=list(context.get("requested_capabilities") or [])
    required=set(context.get("required_capabilities") or [])
    required.add(router_cap)
    all_caps=[router_cap]+[c for c in requested if c!=router_cap]
    resolved=[]; open_items=[]
    write_caps=set(context.get("write_capabilities") or [])

    for cap in all_caps:
        provider,err=select(registry,cap,cap in write_caps)
        if err:
            is_required=cap in required
            open_items.append({
                "open_id":f"OPEN-PROVIDER-{cap}",
                "type":"PROVIDER_CAPABILITY",
                "capability":cap,
                "reason":err,
                "blocks_reasoning":False,
                "blocks_action":is_required,
                "action_scopes":[cap] if is_required else [],
                "severity":"CRITICAL" if is_required else "WARNING",
                "escalation":"ENGINEERING_OWNER" if is_required else "NONE",
            })
            continue
        resolved.append({"capability":cap,"provider_id":provider.get("provider_id"),"provider_type":provider.get("provider_type"),"provider_state":provider.get("provider_state"),"mode":provider.get("mode")})

    human_actions=list(context.get("human_actions") or [])
    blocking_open=[x for x in open_items if x.get("blocks_action") is True]
    blocking_human=[x for x in human_actions if x.get("blocks_action",True)]
    if blocking_open or blocking_human:
        status="ACTION_REQUIRED"
    elif open_items or human_actions:
        status="PARTIAL"
    else:
        status="READY"

    if context.get("write_intent") and not context.get("permission_proof_ref"): errors.append("ROUTE-002: write_intent requires permission_proof_ref")
    if context.get("write_intent") and not context.get("idempotency_key"): errors.append("ROUTE-003: write_intent requires idempotency_key")

    plan={"schema_version":1,"artifact_type":"PROVIDER_RUNTIME_PLAN","runtime_plan":{
        "plan_id":context.get("plan_id","PLAN-RUNTIME-001"),"command":command,
        "project_context":context.get("project_context") or {},"target":context.get("target") or {},
        "requested_capabilities":all_caps,"required_capabilities":sorted(required),
        "resolved_providers":resolved,"human_actions":human_actions,
        "open_items":open_items,"blocking_open_items":[x.get("open_id") for x in blocking_open],
        "executable":not blocking_open and not blocking_human and not errors,
        "write_intent":bool(context.get("write_intent")),"status":"INVALID" if errors else status}}
    return plan,errors

def main():
    p=argparse.ArgumentParser(); p.add_argument("registry",type=Path); p.add_argument("context",type=Path); p.add_argument("-o","--output",type=Path); a=p.parse_args()
    try: plan,errors=build_plan(load(a.registry),load(a.context))
    except Exception as exc: print(f"ROUTE-LOAD: {exc}",file=sys.stderr); return 2
    if errors: print("\n".join(errors),file=sys.stderr); return 1
    text=yaml.safe_dump(plan,allow_unicode=True,sort_keys=False)
    if a.output: a.output.write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
