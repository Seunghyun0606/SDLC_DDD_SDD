#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
from types import SimpleNamespace
from invoke_provider_runtime import invoke_request

def registry(module="fake.adapter",mode="READ_WRITE"):
 return {"registry":{"providers":[{"provider_id":"p","provider_type":"GENERIC","enabled":True,"provider_state":"AVAILABLE","mode":mode,"capabilities":["generic.read","generic.write"],"extensions":{"module":module}}]}}
def request(op="generic.read",write=False):
 return {"provider_request":{"request_id":"REQ-X","provider_type":"GENERIC","operation":op,"project_context":{"project_id":"P","mode":"BROWNFIELD","stage":"DISCOVERY"},"target":{"target_type":"WORK_UNIT","target_id":"W"},"write_intent":write,"expected_revision":"r1" if write else None,"idempotency_key":"idem-1" if write else None,"permission_proof_ref":"perm-1" if write else None,"extensions":{}}}
def response(req,status="OK",retryable=False):
 return {"provider_response":{"request_id":req["provider_request"]["request_id"],"provider_id":"p","provider_type":"GENERIC","operation":req["provider_request"]["operation"],"status":status,"provider_revision":"rev","outputs":[],"evidence":[],"open_items":[] if status in {"OK","PARTIAL"} else [{"code":"X"}],"warnings":[],"retryable":retryable,"extensions":{}}}
def main():
 req=request(); sys.modules["fake.adapter"]=SimpleNamespace(invoke=lambda r,c:response(r,"OK"))
 j,r=invoke_request(registry(),req); assert j["invocation_journal"]["state"]=="SUCCEEDED" and len(j["invocation_journal"]["attempts"])==1
 calls={"n":0}
 def retry(r,c):
  calls["n"]+=1
  return response(r,"BLOCKED",True) if calls["n"]==1 else response(r,"OK")
 sys.modules["fake.adapter"]=SimpleNamespace(invoke=retry); j,r=invoke_request(registry(),req,max_read_attempts=2); assert j["invocation_journal"]["state"]=="SUCCEEDED" and calls["n"]==2
 sys.modules["fake.adapter"]=SimpleNamespace(invoke=lambda r,c:response(r,"PARTIAL")); j,r=invoke_request(registry(),req); assert j["invocation_journal"]["state"]=="PARTIAL"
 def boom(r,c): raise RuntimeError("lost response")
 sys.modules["fake.adapter"]=SimpleNamespace(invoke=boom); w=request("generic.write",True); j,r=invoke_request(registry(),w); assert j["invocation_journal"]["state"]=="UNKNOWN_AFTER_WRITE" and j["invocation_journal"]["recovery"]["required"] is True and len(j["invocation_journal"]["attempts"])==1
 calls["n"]=0
 def write_block(r,c): calls["n"]+=1; return response(r,"BLOCKED",True)
 sys.modules["fake.adapter"]=SimpleNamespace(invoke=write_block); j,r=invoke_request(registry(),w,max_read_attempts=3); assert j["invocation_journal"]["state"]=="BLOCKED" and calls["n"]==1
 bad=request(); bad["provider_request"]["target"]={}; j,r=invoke_request(registry(),bad); assert j["invocation_journal"]["state"]=="BLOCKED" and not j["invocation_journal"]["attempts"]
 root=Path(__file__).resolve().parents[1]; forbidden=["REQ_TM_TE","RQG-CAND-6BB6D66548","근태","AttendanceClose","TB_ATT_","10분"]
 for rel in ["design/contracts/runtime-invocation-recovery.md","config/runtime-invocation.yaml","scripts/invoke_provider_runtime.py"]:
  text=(root/rel).read_text(encoding="utf-8")
  for token in forbidden: assert token not in text,(rel,token)
 print("OK: P0.8 runtime invocation/recovery tests passed")
 return 0
if __name__=="__main__": raise SystemExit(main())
