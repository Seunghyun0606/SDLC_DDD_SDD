#!/usr/bin/env python3
"""Bounded batch/scheduler analyzer. Explicit files only; observations never confirm business truth."""
from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path
from typing import Any
import yaml
CRON=re.compile(r"^\s*([^#\s]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)\s*$")
SCHEDULED=re.compile(r"@Scheduled\s*\((.*?)\)",re.S)
CRON_ARG=re.compile(r'cron\s*=\s*"([^"]+)"')
FIXED=re.compile(r'(fixedRate|fixedDelay|initialDelay)\s*=\s*(?:"([^"]+)"|([0-9]+))')
METHOD=re.compile(r"@Scheduled\s*\([^)]*\)\s*(?:public|protected|private)?\s*[\w<>,?\[\].]+\s+(\w+)\s*\(",re.S)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_cron(text):
 out=[]
 for n,line in enumerate(text.splitlines(),1):
  s=line.strip()
  if not s or s.startswith('#') or ('=' in s.split()[0]): continue
  m=CRON.match(line)
  if m: out.append({'kind':'CRON_ENTRY','line':n,'schedule':' '.join(m.group(i) for i in range(1,6)),'command':m.group(6).strip()})
 return out
def parse_java(text):
 out=[]; methods=METHOD.findall(text)
 for i,m in enumerate(SCHEDULED.finditer(text)):
  args=m.group(1); obj={'kind':'SPRING_SCHEDULED','method':methods[i] if i<len(methods) else None}; c=CRON_ARG.search(args)
  if c: obj.update({'schedule_type':'cron','schedule':c.group(1)})
  fixed={x.group(1):x.group(2) or x.group(3) for x in FIXED.finditer(args)}
  if fixed: obj['fixed']=fixed
  out.append(obj)
 signals=[t for t in ('@EnableBatchProcessing','JobBuilder','StepBuilder','JobLauncher') if t in text]
 if signals: out.append({'kind':'SPRING_BATCH_SIGNAL','signals':signals})
 return out
def parse_yaml(text):
 out=[]; opens=[]
 try: docs=list(yaml.safe_load_all(text))
 except Exception as exc: return [],[{'code':'YAML_PARSE_ERROR','detail':str(exc)}]
 for doc in docs:
  if not isinstance(doc,dict) or str(doc.get('kind') or '').casefold()!='cronjob': continue
  spec=doc.get('spec') or {}; meta=doc.get('metadata') or {}; tmpl=(((spec.get('jobTemplate') or {}).get('spec') or {}).get('template') or {}); containers=(tmpl.get('spec') or {}).get('containers') or []
  out.append({'kind':'KUBERNETES_CRONJOB','name':meta.get('name'),'schedule':spec.get('schedule'),'time_zone':spec.get('timeZone'),'concurrency_policy':spec.get('concurrencyPolicy'),'suspend':spec.get('suspend'),'containers':[{'name':c.get('name'),'image':c.get('image'),'command':c.get('command'),'args':c.get('args')} for c in containers if isinstance(c,dict)]})
 if re.search(r"(?m)^\s*(?:on|['\"]on['\"]):\s*$",text) and re.search(r"(?m)^\s*schedule:\s*$",text):
  out += [{'kind':'GITHUB_ACTIONS_SCHEDULE','schedule':m.group(1).strip()} for m in re.finditer(r"(?m)^\s*-\s*cron:\s*['\"]?([^'\"\n]+)['\"]?\s*$",text)]
 return out,opens
def analyze(root:Path,files:list[str])->dict[str,Any]:
 root=root.resolve(); evidence=[]; opens=[]
 for raw in files:
  p=(root/raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
  try: rel=str(p.relative_to(root))
  except ValueError: raise ValueError(f'path outside root: {p}')
  if not p.is_file(): opens.append({'code':'SOURCE_FILE_NOT_FOUND','path':rel,'truth_state':'OPEN'}); continue
  text=p.read_text(encoding='utf-8',errors='replace'); suffix=p.suffix.casefold(); objs=[]; local=[]
  if suffix in {'.yaml','.yml'}: objs,local=parse_yaml(text)
  elif suffix=='.java': objs=parse_java(text)
  elif p.name.casefold() in {'crontab','cron'} or suffix in {'.cron','.crontab'}: objs=parse_cron(text)
  else: objs=parse_java(text)+parse_cron(text)
  for x in local: x.update({'path':rel,'truth_state':'OPEN'}); opens.append(x)
  evidence.append({'path':rel,'file_sha256':digest(p),'truth_state':'OBSERVED','business_truth_confirmed':False,'objects':objs,'signals':sorted({o.get('kind') for o in objs if o.get('kind')})})
 return {'schema_version':1,'artifact_type':'SOURCE_ANALYSIS_RESULT','source_analysis_result':{'analyzer_id':'batch-scheduler','maturity':'BOUNDED_CONFIG_AND_ANNOTATION_PARSER','evidence':evidence,'open_items':opens,'truth_guards':{'source_schedule_is_not_business_truth':True,'business_truth_auto_confirmation':False,'explicit_file_list_only':True}}}
def main():
 p=argparse.ArgumentParser(); p.add_argument('root',type=Path); p.add_argument('files',nargs='+'); p.add_argument('-o','--output',type=Path); a=p.parse_args(); r=analyze(a.root,a.files); text=yaml.safe_dump(r,allow_unicode=True,sort_keys=False)
 if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding='utf-8')
 else: print(text,end='')
 return 0
if __name__=='__main__': raise SystemExit(main())
