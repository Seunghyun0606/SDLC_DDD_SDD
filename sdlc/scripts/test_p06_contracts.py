#!/usr/bin/env python3
"""Self-contained P0.6 provider/runtime contract tests."""
from copy import deepcopy
from pathlib import Path
from validate_p06_contracts import validate_registry, validate_request, validate_response
from route_provider_command import build_plan

def assert_code(errors,code): assert any(e.startswith(code+":") for e in errors),(code,errors)
def registry_case():
 return {"registry":{"protocol_version":"P0.6-1","providers":[
  {"provider_id":"router","provider_type":"COMMAND_ROUTER","enabled":True,"provider_state":"AVAILABLE","mode":"READ_ONLY","capabilities":["command.route.work","command.route.change","command.route.check"]},
  {"provider_id":"source","provider_type":"SOURCE","enabled":True,"provider_state":"AVAILABLE","mode":"READ_ONLY","capabilities":["source.snapshot.read","source.search","source.diff"]},
  {"provider_id":"test","provider_type":"TEST","enabled":True,"provider_state":"AVAILABLE","mode":"READ_WRITE","capabilities":["test.discover","test.execute","test.result.read"]}]}}
def request_case():
 return {"provider_request":{"request_id":"REQ-1","provider_type":"SOURCE","operation":"source.snapshot.read","project_context":{"project_id":"P","mode":"BROWNFIELD","stage":"DISCOVERY"},"target":{"target_type":"WORK_UNIT","target_id":"W1"},"write_intent":False,"extensions":{"language":"python"}}}
def response_case():
 return {"provider_response":{"request_id":"REQ-1","provider_id":"source","provider_type":"SOURCE","operation":"source.snapshot.read","status":"OK","provider_revision":"abc123","outputs":[],"evidence":[{"evidence_id":"EV-1","truth":"OBSERVED","locator":"src/module.py","revision":"abc123","observed_value":"symbol"}],"open_items":[],"warnings":[],"extensions":{"framework":"fastapi"}}}
def main():
 reg=registry_case(); assert validate_registry(reg)==[]
 req=request_case(); assert validate_request(req,reg)==[]
 res=response_case(); assert validate_response(res,req,reg)==[]
 bad=deepcopy(req); bad["provider_request"]["write_intent"]=True; assert_code(validate_request(bad,reg),"P06-026"); assert_code(validate_request(bad,reg),"P06-029")
 bad=deepcopy(res); bad["provider_response"]["evidence"][0]["truth"]="CONFIRMED"; assert_code(validate_response(bad,req,reg),"P06-047")
 green={"command":"/work","project_context":{"project_id":"G","mode":"GREENFIELD","stage":"DESIGN"},"target":{"target_type":"WORK_UNIT","target_id":"G-1"},"requested_capabilities":[]}
 plan,errors=build_plan(reg,green); assert errors==[] and plan["runtime_plan"]["status"]=="READY"
 brown={"command":"/work","project_context":{"project_id":"B","mode":"BROWNFIELD","stage":"DISCOVERY"},"target":{"target_type":"WORK_UNIT","target_id":"B-1"},"requested_capabilities":["source.snapshot.read","source.search"]}
 plan,errors=build_plan(reg,brown); assert errors==[] and plan["runtime_plan"]["status"]=="READY"; assert {x["provider_type"] for x in plan["runtime_plan"]["resolved_providers"]}=={"COMMAND_ROUTER","SOURCE"}
 test=deepcopy(brown); test["project_context"]["stage"]="TEST"; test["requested_capabilities"]=["test.discover","test.execute"]; plan,errors=build_plan(reg,test); assert errors==[] and plan["runtime_plan"]["status"]=="READY"; assert any(x["provider_type"]=="TEST" for x in plan["runtime_plan"]["resolved_providers"])
 unsupported=deepcopy(brown); unsupported["requested_capabilities"]=["deployment.release.execute"]; plan,errors=build_plan(reg,unsupported); assert plan["runtime_plan"]["status"]=="ACTION_REQUIRED"; assert plan["runtime_plan"]["open_items"][0]["reason"]=="MISSING_CAPABILITY"
 unconfigured=deepcopy(reg); unconfigured["registry"]["providers"][1]["provider_state"]="UNCONFIGURED"; plan,errors=build_plan(unconfigured,brown); assert plan["runtime_plan"]["status"]=="ACTION_REQUIRED"; assert any(x["reason"]=="PROVIDER_UNAVAILABLE" for x in plan["runtime_plan"]["open_items"])
 with_human=deepcopy(green); with_human["human_actions"]=[{"action_type":"BUSINESS_DECISION","owner":"HUMAN"}]; plan,errors=build_plan(reg,with_human); assert plan["runtime_plan"]["status"]=="ACTION_REQUIRED"
 root=Path(__file__).resolve().parents[1]; core=[root/"config/provider-registry.example.yaml",root/"templates/provider-request.yaml",root/"templates/provider-response.yaml",root/"templates/provider-runtime-plan.yaml",root/"scripts/validate_p06_contracts.py",root/"scripts/route_provider_command.py"]
 forbidden=["REQ_TM_TE","RQG-CAND-6BB6D66548","근태","AttendanceClose","TB_ATT_","10분"]
 for path in core:
  text=path.read_text(encoding="utf-8")
  for token in forbidden: assert token not in text,(path,token)
 print("OK: P0.6 provider/runtime contract tests passed"); return 0
if __name__=="__main__": raise SystemExit(main())
