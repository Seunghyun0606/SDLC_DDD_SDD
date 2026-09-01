#!/usr/bin/env python3
"""Bounded Java/Spring analyzer adapter for explicitly supplied files."""
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path
from typing import Any
import yaml

ANNOTATIONS = ["RestController","Controller","Service","Repository","Component","Transactional","Autowired"]
CLASS_RE = re.compile(r"\b(class|interface|enum|record)\s+([A-Za-z_$][\w$]*)")
METHOD_RE = re.compile(r"\b(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?[\w<>,.?\[\] ]+\s+([A-Za-z_$][\w$]*)\s*\(")
ROUTE_RE = re.compile(r"@(RequestMapping|GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\s*(?:\(\s*(?:value\s*=\s*|path\s*=\s*)?([\"'][^\"']+[\"']))?")

def analyze_file(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    annotations = sorted({name for name in ANNOTATIONS if re.search(rf"@{re.escape(name)}\b", text)})
    routes = []
    for kind, raw in ROUTE_RE.findall(text):
        routes.append({"annotation": kind, "path": raw[1:-1] if raw else None})
    classes = [{"kind": k, "name": n} for k, n in CLASS_RE.findall(text)]
    methods = sorted(set(METHOD_RE.findall(text)))
    signals = []
    if routes: signals.append("spring_route")
    if "Transactional" in annotations: signals.append("spring_transaction")
    if "Autowired" in annotations or re.search(r"\bfinal\s+[A-Z][\w<>?, ]+\s+\w+\s*;", text): signals.append("dependency_injection")
    return {
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "truth_state": "OBSERVED",
        "classes": classes,
        "methods": methods,
        "annotations": annotations,
        "routes": routes,
        "signals": signals,
        "business_truth_confirmed": False,
    }

def analyze(root: Path, files: list[str]) -> dict[str, Any]:
    evidence=[]; open_items=[]
    for rel in files:
        path=(root/rel).resolve()
        try: path.relative_to(root.resolve())
        except ValueError: raise ValueError(f"target escapes source root: {rel}")
        if not path.exists() or not path.is_file():
            open_items.append({"open_id":f"OPEN-JAVA-{rel}","type":"SOURCE_FILE_MISSING","path":rel,"blocks_reasoning":False,"blocks_action":False})
            continue
        evidence.append(analyze_file(path, root.resolve()))
    return {"schema_version":1,"artifact_type":"SOURCE_ANALYSIS_RESULT","source_analysis_result":{
        "analyzer_id":"java-spring","bounded":True,"requested_files":files,"evidence":evidence,"open_items":open_items,
        "truth_guards":{"source_behavior_is_not_business_truth":True,"name_similarity_does_not_confirm_trace":True}}}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("source_root",type=Path); p.add_argument("--file",action="append",required=True); p.add_argument("-o","--output",type=Path); a=p.parse_args()
    result=analyze(a.source_root,a.file); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
    if a.output:a.output.write_text(text,encoding="utf-8")
    else:print(text,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
