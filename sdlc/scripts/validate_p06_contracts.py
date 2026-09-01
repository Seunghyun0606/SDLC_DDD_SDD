#!/usr/bin/env python3
"""Deterministic validators for P0.6 provider/runtime contracts."""
from __future__ import annotations
import argparse,re,sys
from pathlib import Path
from typing import Any
import yaml
MODES={"AUTO","GREENFIELD","BROWNFIELD","HYBRID"}; WRITE_MODES={"READ_ONLY","READ_WRITE"}; PROVIDER_STATES={"AVAILABLE","DEGRADED","UNAVAILABLE","UNCONFIGURED","DISABLED"}; RESPONSE_STATUSES={"OK","PARTIAL","BLOCKED","ERROR"}; TRUTH={"GIVEN","OBSERVED","INFERRED","CONFIRMED","OPEN"}; CAPABILITY=re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*){1,}$"); PROVIDER_TYPE=re.compile(r"^[A-Z][A-Z0-9_]*$")
def add(e,c,m): e.append(f"{c}: {m}")
def load_yaml(p:Path)->dict[str,Any]: return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
def registry_root(d): return (d or {}).get("registry") or {}
def provider_index(d): return {p.get("provider_id"):p for p in registry_root(d).get("providers") or [] if p.get("provider_id")}
def valid_provider_type(value): return bool(PROVIDER_TYPE.match(str(value or "")))
def validate_registry(data):
 e=[]; root=registry_root(data); providers=root.get("providers") or []
 if not root:return ["P06-001: registry is required"]
 if not providers:return ["P06-002: at least one provider is required"]
 seen=set()
 for i,p in enumerate(providers):
  pid=p.get("provider_id")
  if not pid:add(e,"P06-003",f"providers[{i}].provider_id is required")
  elif pid in seen:add(e,"P06-004",f"duplicate provider_id: {pid}")
  else:seen.add(pid)
  if not valid_provider_type(p.get("provider_type")):add(e,"P06-005",f"providers[{i}].provider_type is invalid")
  if p.get("mode") not in WRITE_MODES:add(e,"P06-006",f"providers[{i}].mode is invalid")
  if p.get("provider_state") not in PROVIDER_STATES:add(e,"P06-010",f"providers[{i}].provider_state is invalid")
  caps=p.get("capabilities") or []
  if len(caps)!=len(set(caps)):add(e,"P06-007",f"providers[{i}] has duplicate capabilities")
  for c in caps:
   if not CAPABILITY.match(str(c)):add(e,"P06-008",f"invalid capability name: {c}")
 return e
def validate_request(data,registry=None):
 e=[]; req=(data or {}).get("provider_request")
 if not isinstance(req,dict):return ["P06-020: provider_request is required"]
 for k in ("request_id","provider_type","operation","project_context","target"):
  if req.get(k) in (None,"",{}):add(e,"P06-021",f"provider_request.{k} is required")
 if not valid_provider_type(req.get("provider_type")):add(e,"P06-022","provider_type is invalid")
 if not CAPABILITY.match(str(req.get("operation",""))):add(e,"P06-023","operation must use capability naming")
 if (req.get("project_context") or {}).get("mode") not in MODES:add(e,"P06-024","project_context.mode is invalid")
 t=req.get("target") or {}
 if not t.get("target_type") or not t.get("target_id"):add(e,"P06-025","target_type and target_id are required")
 if req.get("write_intent") is True:
  for k in ("expected_revision","idempotency_key","permission_proof_ref"):
   if not req.get(k):add(e,"P06-026",f"write request requires {k}")
 if registry:
  c=[p for p in registry_root(registry).get("providers") or [] if p.get("enabled") is True and p.get("provider_state") in {"AVAILABLE","DEGRADED"} and p.get("provider_type")==req.get("provider_type") and req.get("operation") in (p.get("capabilities") or [])]
  if not c:add(e,"P06-028","no usable provider advertises requested capability")
  if req.get("write_intent") is True and c and not any(p.get("mode")=="READ_WRITE" for p in c):add(e,"P06-029","write intent requires READ_WRITE provider")
 return e
def validate_response(data,request=None,registry=None):
 e=[]; res=(data or {}).get("provider_response")
 if not isinstance(res,dict):return ["P06-040: provider_response is required"]
 for k in ("request_id","provider_id","provider_type","operation","status","provider_revision"):
  if not res.get(k):add(e,"P06-041",f"provider_response.{k} is required")
 if not valid_provider_type(res.get("provider_type")):add(e,"P06-042","response provider_type is invalid")
 if res.get("status") not in RESPONSE_STATUSES:add(e,"P06-043","response status is invalid")
 if res.get("status") in {"BLOCKED","ERROR"} and not (res.get("open_items") or res.get("warnings")):add(e,"P06-044","BLOCKED/ERROR response needs open_items or warnings")
 for i,ev in enumerate(res.get("evidence") or []):
  for k in ("evidence_id","truth","locator","revision"):
   if not ev.get(k):add(e,"P06-045",f"evidence[{i}].{k} is required")
  if ev.get("truth") not in TRUTH:add(e,"P06-046",f"evidence[{i}].truth is invalid")
  if res.get("provider_type") in {"SOURCE","TEST"} and ev.get("truth")=="CONFIRMED":add(e,"P06-047","SOURCE/TEST provider evidence must not promote business truth to CONFIRMED")
 if not isinstance(res.get("extensions",{}),dict):add(e,"P06-048","extensions must be an object")
 if request:
  req=(request or {}).get("provider_request") or {}
  if res.get("request_id")!=req.get("request_id"):add(e,"P06-049","request_id correlation mismatch")
  if res.get("provider_type")!=req.get("provider_type"):add(e,"P06-050","provider_type correlation mismatch")
  if res.get("operation")!=req.get("operation"):add(e,"P06-051","operation correlation mismatch")
 if registry:
  p=provider_index(registry).get(res.get("provider_id"))
  if not p:add(e,"P06-052","response provider_id not found in registry")
  else:
   if p.get("provider_type")!=res.get("provider_type"):add(e,"P06-053","registry provider_type mismatch")
   if res.get("operation") not in (p.get("capabilities") or []):add(e,"P06-054","provider did not advertise response operation")
   if p.get("provider_state") not in {"AVAILABLE","DEGRADED"}:add(e,"P06-055","response came from unusable provider state")
 return e
def main():
 p=argparse.ArgumentParser(); p.add_argument("kind",choices=["registry","request","response"]); p.add_argument("path",type=Path); p.add_argument("--registry",type=Path); p.add_argument("--request",type=Path); a=p.parse_args()
 try:d=load_yaml(a.path); r=load_yaml(a.registry) if a.registry else None; q=load_yaml(a.request) if a.request else None
 except Exception as x:print(f"P06-LOAD: {x}",file=sys.stderr);return 2
 e=validate_registry(d) if a.kind=="registry" else validate_request(d,r) if a.kind=="request" else validate_response(d,q,r)
 if e:print("\n".join(e),file=sys.stderr);return 1
 print(f"OK: P0.6 {a.kind} contract valid: {a.path}");return 0
if __name__=="__main__":raise SystemExit(main())
