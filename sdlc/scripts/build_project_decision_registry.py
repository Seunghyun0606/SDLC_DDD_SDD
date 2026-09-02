#!/usr/bin/env python3
"""Build one project decision registry from the bootstrap result and decision authority."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml

VALID_STATES={"OPEN","CANDIDATE","CONFIRMED","NOT_APPLICABLE","SUPERSEDED"}
VALID_TRUTH={"GIVEN","OBSERVED","INFERRED","CONFIRMED","OPEN"}

def load(path:Path)->dict[str,Any]: return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def validate(doc:dict[str,Any],config:dict[str,Any])->list[str]:
    errors=[]; defs=config.get("decisions") or {}; root=(doc or {}).get("project_decisions") or {}; items=root.get("decisions") or {}
    if not root.get("project_id"): errors.append("P1D-001 project_id required")
    if set(items)!=set(defs):
        missing=sorted(set(defs)-set(items)); unknown=sorted(set(items)-set(defs))
        if missing: errors.append("P1D-002 missing decisions: "+", ".join(missing))
        if unknown: errors.append("P1D-003 unknown decisions: "+", ".join(unknown))
    for key,item in items.items():
        if key not in defs: continue
        state=item.get("state"); truth=item.get("truth_state")
        if state not in VALID_STATES: errors.append(f"P1D-010 {key}: invalid state")
        if truth not in VALID_TRUTH: errors.append(f"P1D-011 {key}: invalid truth_state")
        if state=="CONFIRMED":
            if item.get("value") in (None,""): errors.append(f"P1D-012 {key}: confirmed value required")
            if not item.get("owner"): errors.append(f"P1D-013 {key}: confirmed owner required")
            if not item.get("basis"): errors.append(f"P1D-014 {key}: confirmed basis required")
            if not item.get("evidence_refs") and truth!="GIVEN": errors.append(f"P1D-015 {key}: evidence or GIVEN source required")
        if state=="CANDIDATE" and item.get("candidate_value") in (None,""): errors.append(f"P1D-016 {key}: candidate_value required")
    return errors

def build(bootstrap:dict[str,Any],config:dict[str,Any])->dict[str,Any]:
    boot=(bootstrap or {}).get("project_bootstrap") or {}; project_id=boot.get("project_id"); mode=boot.get("resolved_mode") or boot.get("mode")
    if not project_id or mode not in {"GREENFIELD","BROWNFIELD","HYBRID","AUTO"}: raise ValueError("project bootstrap requires project_id and resolved mode")
    prior={str(x.get("decision_key")):x for x in (boot.get("technology_decisions") or []) if x.get("decision_key")}
    items={}; blockers=[]; open_items=[]
    for key,spec in (config.get("decisions") or {}).items():
        applicable=mode=="AUTO" or mode in (spec.get("applies_to") or [])
        old=prior.get(key) or {}; state=str(old.get("state") or ("OPEN" if applicable else "NOT_APPLICABLE"))
        if not applicable: state="NOT_APPLICABLE"
        item={"state":state,"value":old.get("confirmed_value") if old.get("confirmed_value") is not None else old.get("value"),
              "candidate_value":old.get("candidate") if old.get("candidate") is not None else old.get("candidate_value"),
              "owner":old.get("owner") or "","truth_state":str(old.get("truth_state") or "OPEN"),"basis":old.get("decision_basis") or old.get("basis") or "",
              "evidence_refs":list(old.get("evidence_refs") or [])}
        items[key]=item
        if applicable and state!="CONFIRMED":
            open_id=f"OPEN-DECISION-{key.upper()}"; actions=list(spec.get("blocking_actions") or [])
            open_items.append({"open_id":open_id,"type":"PROJECT_DECISION","decision_key":key,"label_ko":spec.get("label_ko") or key,
                               "blocks_reasoning":False,"blocks_action":bool(actions),"action_scopes":actions,"escalation":spec.get("owner_role") or "ARCHITECT_OR_ENGINEERING_OWNER"})
            blockers.extend({"decision_key":key,"action":action,"state":state,"open_id":open_id} for action in actions)
    out={"version":1,"project_decisions":{"project_id":project_id,"project_mode":mode,"revision":1,"decisions":items,"action_blockers":blockers,"open_items":open_items,
         "truth_guards":{"candidate_is_not_confirmed":True,"source_observation_does_not_auto_confirm":True,"open_is_not_auto_filled":True}}}
    errors=validate(out,config)
    if errors: raise ValueError("; ".join(errors))
    return out

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("bootstrap",type=Path); p.add_argument("config",type=Path); p.add_argument("-o","--output",type=Path,required=True); a=p.parse_args()
    out=build(load(a.bootstrap),load(a.config)); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(yaml.safe_dump(out,allow_unicode=True,sort_keys=False),encoding="utf-8")
    root=out["project_decisions"]; print(f"OK: decisions={len(root['decisions'])} action_blockers={len(root['action_blockers'])}"); return 0
if __name__=="__main__": raise SystemExit(main())
