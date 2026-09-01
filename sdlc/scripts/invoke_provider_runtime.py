#!/usr/bin/env python3
"""Invoke one P0.6 provider request with P0.8 journal/recovery guards."""
from __future__ import annotations
import argparse, importlib, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml
from validate_p06_contracts import validate_request, validate_response

USABLE={"AVAILABLE","DEGRADED"}

def now(): return datetime.now(timezone.utc).isoformat()
def load(p:Path): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

def select_provider(registry, req):
    root=(registry or {}).get("registry") or {}
    candidates=[]
    for p in root.get("providers") or []:
        if p.get("enabled") is not True or p.get("provider_state") not in USABLE: continue
        if p.get("provider_type")!=req.get("provider_type"): continue
        if req.get("operation") not in (p.get("capabilities") or []): continue
        if req.get("write_intent") and p.get("mode")!="READ_WRITE": continue
        candidates.append(p)
    candidates=sorted(candidates,key=lambda p:(int(p.get("priority",100)),str(p.get("provider_id"))))
    if not candidates: return None,"NO_USABLE_PROVIDER"
    if len(candidates)>1 and int(candidates[0].get("priority",100))==int(candidates[1].get("priority",100)): return None,"AMBIGUOUS_PROVIDER"
    return candidates[0],None

def invoke_request(registry, request_doc, adapter_configs=None, max_read_attempts=2):
    req=(request_doc or {}).get("provider_request") or {}
    req_errors=validate_request(request_doc,registry)
    journal={"schema_version":1,"artifact_type":"INVOCATION_JOURNAL","invocation_journal":{
        "journal_id":f"JOURNAL-{req.get('request_id','UNKNOWN')}","request_id":req.get("request_id"),
        "provider_id":None,"operation":req.get("operation"),"write_intent":bool(req.get("write_intent")),
        "state":"PLANNED","attempts":[],"recovery":{"required":False,"reason":None,"idempotency_key":req.get("idempotency_key"),"evidence":[]},
        "final_response_status":None,"open_items":[]}}
    jr=journal["invocation_journal"]
    if req_errors:
        jr["state"]="BLOCKED"; jr["open_items"]=[{"code":"REQUEST_INVALID","details":req_errors}]
        return journal,None
    provider,problem=select_provider(registry,req)
    if problem:
        jr["state"]="BLOCKED"; jr["open_items"]=[{"code":problem}]
        return journal,None
    jr["provider_id"]=provider.get("provider_id")
    module_name=((provider.get("extensions") or {}).get("module"))
    if not module_name:
        jr["state"]="BLOCKED"; jr["open_items"]=[{"code":"ADAPTER_MODULE_UNCONFIGURED"}]
        return journal,None
    try: module=importlib.import_module(module_name)
    except Exception as exc:
        jr["state"]="BLOCKED"; jr["open_items"]=[{"code":"ADAPTER_LOAD_FAILED","message":str(exc)}]
        return journal,None
    if not callable(getattr(module,"invoke",None)):
        jr["state"]="BLOCKED"; jr["open_items"]=[{"code":"ADAPTER_PROTOCOL_INVALID"}]
        return journal,None
    config=(adapter_configs or {}).get(provider.get("provider_id"),{})
    max_attempts=1 if req.get("write_intent") else max(1,int(max_read_attempts))
    final=None
    for attempt_no in range(1,max_attempts+1):
        started=now(); jr["state"]="STARTED"
        attempt={"attempt_no":attempt_no,"started_at":started,"finished_at":None,"response_status":None,"retryable":False,"error":None}
        jr["attempts"].append(attempt)
        try:
            response=module.invoke(request_doc,config)
        except Exception as exc:
            attempt["finished_at"]=now(); attempt["error"]={"code":"ADAPTER_EXCEPTION","message":str(exc)}
            if req.get("write_intent"):
                jr["state"]="UNKNOWN_AFTER_WRITE"; jr["recovery"].update({"required":True,"reason":"adapter exception after write dispatch"})
                jr["open_items"]=[{"code":"WRITE_RECOVERY_REQUIRED"}]
                return journal,None
            if attempt_no<max_attempts: continue
            jr["state"]="FAILED"; jr["open_items"]=[{"code":"ADAPTER_EXCEPTION","message":str(exc)}]
            return journal,None
        attempt["finished_at"]=now()
        errors=validate_response(response,request_doc,registry)
        if errors:
            attempt["error"]={"code":"RESPONSE_INVALID","details":errors}; jr["state"]="FAILED"; jr["open_items"]=[attempt["error"]]
            return journal,response
        res=response["provider_response"]; status=res.get("status"); retryable=bool(res.get("retryable"))
        attempt["response_status"]=status; attempt["retryable"]=retryable; final=response; jr["final_response_status"]=status
        if status=="OK": jr["state"]="SUCCEEDED"; return journal,response
        if status=="PARTIAL": jr["state"]="PARTIAL"; return journal,response
        if status in {"BLOCKED","ERROR"} and retryable and not req.get("write_intent") and attempt_no<max_attempts: continue
        jr["state"]="BLOCKED" if status=="BLOCKED" else "FAILED"
        jr["open_items"]=res.get("open_items") or [{"code":"PROVIDER_"+str(status)}]
        return journal,response
    jr["state"]="FAILED"; return journal,final

def main():
    p=argparse.ArgumentParser(); p.add_argument("registry",type=Path); p.add_argument("request",type=Path); p.add_argument("--config",type=Path); p.add_argument("--max-read-attempts",type=int,default=2); p.add_argument("-o","--output",type=Path); a=p.parse_args()
    cfg=load(a.config) if a.config else {}; configs=(cfg.get("adapter_configs") or cfg)
    journal,response=invoke_request(load(a.registry),load(a.request),configs,a.max_read_attempts)
    out={"journal":journal,"response":response}; text=yaml.safe_dump(out,allow_unicode=True,sort_keys=False)
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    state=journal["invocation_journal"]["state"]
    return 0 if state in {"SUCCEEDED","PARTIAL"} else 1
if __name__=="__main__": raise SystemExit(main())
