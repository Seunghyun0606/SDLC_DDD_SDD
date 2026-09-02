#!/usr/bin/env python3
"""Resolve project overlays through an explicit semantic allowlist and fail-closed activation rules."""
from __future__ import annotations
import argparse,copy,sys
from pathlib import Path
from typing import Any
import yaml

TRUTH={"GIVEN","OBSERVED","INFERRED","CONFIRMED","OPEN"}
DEFAULT_SCHEMA=Path(__file__).resolve().parents[1]/"config"/"overlay-schema.yaml"
def load_yaml(path): return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
def get_path(doc:dict[str,Any],dotted:str):
    cur:Any=doc
    for part in dotted.split("."):
        if not isinstance(cur,dict) or part not in cur: return False,None
        cur=cur[part]
    return True,cur
def set_existing_path(doc:dict[str,Any],dotted:str,value:Any):
    parts=dotted.split("."); cur=doc
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part],dict): raise KeyError(dotted)
        cur=cur[part]
    if parts[-1] not in cur: raise KeyError(dotted)
    cur[parts[-1]]=value
def rule_for(schema,key):
    exact=(schema.get("allowed_targets") or {}).get(key)
    if exact: return exact,False
    for row in schema.get("allowed_prefixes") or []:
        if key.startswith(str(row.get("prefix") or "")): return row,True
    return None,False
def protected(schema,key): return any(key.startswith(str(p)) for p in schema.get("protected_prefixes") or [])
def type_ok(rule,value):
    kind=rule.get("type","any")
    if kind=="any": return True
    if kind=="string": return isinstance(value,str)
    if kind=="list": return isinstance(value,list)
    if kind=="bool": return isinstance(value,bool)
    if kind=="number": return isinstance(value,(int,float)) and not isinstance(value,bool)
    if kind=="enum": return value in (rule.get("values") or [])
    return False
def activation_errors(root,schema):
    policy=schema.get("policy") or {}; errors=[]; scope=root.get("scope") or {}; trigger=root.get("trigger") or {}; basis=root.get("basis") or {}; lifecycle=root.get("lifecycle") or {}
    if policy.get("active_requires_project_scope") and not scope.get("project_id"): errors.append("scope.project_id required")
    if policy.get("active_requires_reason") and not trigger.get("reason"): errors.append("trigger.reason required")
    if policy.get("active_requires_revision") and (not isinstance(root.get("revision"),int) or root.get("revision",0)<1): errors.append("positive integer revision required")
    truth=basis.get("truth_state")
    if truth not in TRUTH: errors.append("basis.truth_state invalid")
    if policy.get("active_requires_evidence_or_given_source"):
        supported=bool(basis.get("evidence_ids") or basis.get("source_refs")) or (truth=="GIVEN" and bool(basis.get("project_fact")))
        if not supported: errors.append("basis evidence/source_ref or GIVEN project_fact required")
    if policy.get("active_requires_activated_by_and_at") and (not lifecycle.get("activated_by") or not lifecycle.get("activated_at")): errors.append("lifecycle.activated_by/activated_at required")
    return errors
def resolve(profile,overlays,schema):
    resolved=copy.deepcopy(profile); applied=[]; skipped=[]
    for path,doc in overlays:
        root=(doc or {}).get("overlay") or {}; oid=root.get("overlay_id") or path
        if root.get("state")!="ACTIVE": skipped.append({"overlay_id":oid,"reason":"NOT_ACTIVE"}); continue
        errors=activation_errors(root,schema); safety=root.get("safety") or {}
        if safety.get("copies_core_truth") or safety.get("sample_specific_only"): errors.append("unsafe overlay safety flags")
        change=root.get("change") or {}; key=str(change.get("target_key") or "")
        if not key: errors.append("target_key missing")
        if key and protected(schema,key): errors.append(f"protected target_key: {key}")
        rule,is_prefix=rule_for(schema,key) if key else (None,False)
        if key and not rule: errors.append(f"unknown target_key denied: {key}")
        value=change.get("project_value")
        if rule and not type_ok(rule,value): errors.append(f"type/value mismatch for {key}")
        exists,current=get_path(resolved,key) if key else (False,None)
        if rule and not exists and not is_prefix: errors.append(f"target path does not exist: {key}")
        if exists and "core_or_profile_value" in change and change.get("core_or_profile_value")!=current: errors.append(f"stale base value for {key}")
        if errors: raise ValueError(f"{oid}: "+"; ".join(errors))
        if exists: set_existing_path(resolved,key,value)
        else:
            parts=key.split("."); parent=".".join(parts[:-1]); ok,parent_value=get_path(resolved,parent)
            if not ok or not isinstance(parent_value,dict): raise ValueError(f"{oid}: prefix parent path does not exist: {parent}")
            parent_value[parts[-1]]=value
        applied.append({"overlay_id":oid,"target_key":key,"revision":root.get("revision"),"previous_value":current,"project_value":value})
    return resolved,{"strategy":"LATE_BOUND_OVERLAY_SCHEMA_SAFE","applied":applied,"skipped":skipped}
def main():
    p=argparse.ArgumentParser(); p.add_argument("profile",type=Path); p.add_argument("overlays",nargs="*",type=Path); p.add_argument("--schema",type=Path,default=DEFAULT_SCHEMA); p.add_argument("-o","--output",required=True,type=Path); a=p.parse_args()
    try: resolved,report=resolve(load_yaml(a.profile),[(str(x),load_yaml(x)) for x in a.overlays],load_yaml(a.schema))
    except Exception as exc: print(f"DENY: {exc}",file=sys.stderr); return 2
    out={"resolved_project_configuration":resolved,"overlay_resolution":{**report,"generated_from":str(a.profile)}}; a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(yaml.safe_dump(out,allow_unicode=True,sort_keys=False),encoding="utf-8")
    print(f"OK: wrote {a.output}; applied={len(report['applied'])} skipped={len(report['skipped'])}"); return 0
if __name__=="__main__": raise SystemExit(main())
