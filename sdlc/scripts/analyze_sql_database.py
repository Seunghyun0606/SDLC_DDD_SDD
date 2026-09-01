#!/usr/bin/env python3
"""Bounded SQL/database analyzer adapter for explicitly supplied files."""
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path
from typing import Any
import yaml

CREATE_RE = re.compile(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(TABLE|VIEW|PROCEDURE|FUNCTION|TRIGGER|SEQUENCE|INDEX)\s+([\w.$\"`]+)", re.I)
REF_RE = re.compile(r"\b(?:FROM|JOIN|UPDATE|INTO|MERGE\s+INTO)\s+([\w.$\"`]+)", re.I)

def clean(name:str)->str: return name.strip('"`')

def analyze_file(path:Path, root:Path)->dict[str,Any]:
    text=path.read_text(encoding="utf-8",errors="replace")
    objects=[{"kind":k.upper(),"name":clean(n)} for k,n in CREATE_RE.findall(text)]
    refs=sorted({clean(n) for n in REF_RE.findall(text)})
    dynamic=bool(re.search(r"\bEXECUTE\s+IMMEDIATE\b|\bsp_executesql\b|\$\{|#\{",text,re.I))
    signals=[]
    if any(x["kind"] in {"TABLE","VIEW"} for x in objects): signals.append("schema_object_definition")
    if any(x["kind"] in {"PROCEDURE","FUNCTION","TRIGGER"} for x in objects): signals.append("database_program_definition")
    if refs: signals.append("data_reference")
    if dynamic: signals.append("dynamic_sql_possible")
    return {"path":str(path.relative_to(root)).replace("\\","/"),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"truth_state":"OBSERVED","objects":objects,"referenced_objects":refs,"dynamic_sql_possible":dynamic,"signals":signals,"business_truth_confirmed":False}

def analyze(root:Path,files:list[str])->dict[str,Any]:
    evidence=[]; open_items=[]
    for rel in files:
        path=(root/rel).resolve()
        try:path.relative_to(root.resolve())
        except ValueError:raise ValueError(f"target escapes source root: {rel}")
        if not path.exists() or not path.is_file():
            open_items.append({"open_id":f"OPEN-SQL-{rel}","type":"SOURCE_FILE_MISSING","path":rel,"blocks_reasoning":False,"blocks_action":False}); continue
        evidence.append(analyze_file(path,root.resolve()))
    return {"schema_version":1,"artifact_type":"SOURCE_ANALYSIS_RESULT","source_analysis_result":{"analyzer_id":"sql-database","bounded":True,"requested_files":files,"evidence":evidence,"open_items":open_items,"truth_guards":{"source_behavior_is_not_business_truth":True,"dynamic_sql_requires_followup_evidence":True}}}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("source_root",type=Path); p.add_argument("--file",action="append",required=True); p.add_argument("-o","--output",type=Path); a=p.parse_args()
    result=analyze(a.source_root,a.file); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0
if __name__=="__main__":raise SystemExit(main())
