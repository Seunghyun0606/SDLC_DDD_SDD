#!/usr/bin/env python3
"""Register GIVEN source requirements as non-canonical work items without silently overwriting changed source content."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, re
from pathlib import Path
from typing import Any
import yaml
def load(path:Path)->dict[str,Any]: return (yaml.safe_load(path.read_text(encoding='utf-8')) or {}) if path.exists() else {}
def dump(path:Path,doc): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(doc,allow_unicode=True,sort_keys=False),encoding='utf-8')
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def clean(v): return '' if v is None else str(v).strip()
def safe_id(v): return re.sub(r'[^A-Za-z0-9_.-]+','-',v).strip('-') or hashlib.sha256(v.encode()).hexdigest()[:12]
def signature(src,rec):
 fields=[src.get('source_revision'),src.get('worksheet'),rec.get('source_row'),rec.get('source_requirement_id'),rec.get('requirement_name'),rec.get('requirement_text'),rec.get('level1'),rec.get('level2')]
 return hashlib.sha256('\x1f'.join(clean(x) for x in fields).encode()).hexdigest()
def register(intake_doc,canonical_doc,ledger_doc,config):
 intake=intake_doc.get('requirement_intake') or {}; src=intake.get('source') or {}; records=intake.get('records') or []
 if intake.get('duplicate_source_requirement_ids'): return canonical_doc,ledger_doc,{'state':'DENY','code':'DUPLICATE_SOURCE_REQUIREMENT_ID','items':[]},2
 can=canonical_doc.setdefault('worklist_canonical',{}); items=can.setdefault('items',[]); by={clean(x.get('work_item_id')):x for x in items if isinstance(x,dict)}
 led=ledger_doc.setdefault('requirement_worklist_registration',{}); entries=led.setdefault('entries',{}); added=[]; unchanged=[]; review=[]; prefix=clean(config.get('work_item_id_prefix')) or 'SRCREQ-'; defaults=config.get('defaults') or {}
 for rec in records:
  sid=clean(rec.get('source_requirement_id'))
  if not sid: review.append({'code':'SOURCE_REQUIREMENT_ID_MISSING','source_row':rec.get('source_row')}); continue
  wid=prefix+safe_id(sid); sig=signature(src,rec); prior=entries.get(wid) or {}; existing=by.get(wid)
  if existing:
   if clean(existing.get('requirement_id'))!=sid: review.append({'code':'WORK_ITEM_ID_COLLISION','work_item_id':wid,'source_requirement_id':sid}); continue
   if prior.get('source_signature')==sig: unchanged.append(wid); continue
   review.append({'code':'SOURCE_REQUIREMENT_CHANGED_REVIEW_REQUIRED','work_item_id':wid,'source_requirement_id':sid,'previous_signature':prior.get('source_signature'),'current_signature':sig}); continue
  note=f"GIVEN source requirement; source={clean(src.get('file_name'))}; worksheet={clean(src.get('worksheet'))}; row={clean(rec.get('source_row'))}; source_revision={clean(src.get('source_revision'))}"
  item={'work_item_id':wid,'parent_id':'','requirement_id':sid,'item_type':defaults.get('item_type','SOURCE_REQUIREMENT'),'name':clean(rec.get('requirement_name')) or sid,'stage':defaults.get('stage','DECOMPOSE'),'status':defaults.get('status','READY_FOR_REVIEW'),'quality':defaults.get('quality','OPEN'),'validity':defaults.get('validity','CANDIDATE'),'assignee':'','planned_start':'','planned_end':'','estimated_effort':'','actual_start':'','actual_end':'','actual_effort':'','dependency_ids':'','program_ids':'','acceptance_test_ids':'','alerts':defaults.get('alerts','Canonical RQ boundary review required; do not auto-confirm from intake'),'updated_at':now(),'revision':'1','note':note}
  items.append(item); by[wid]=item; entries[wid]={'source_requirement_id':sid,'source_signature':sig,'source_revision':src.get('source_revision'),'source_row':rec.get('source_row'),'registered_at':now(),'truth_state':'GIVEN','canonical_rq_created':False}; added.append(wid)
 can['item_count']=len(items); can['registration_guard']={'source_requirement_is_not_canonical_rq':True}; led['schema_version']=1; led['source_file']=src.get('file_name'); led['source_revision']=src.get('source_revision')
 state='ACTION_REQUIRED' if review else 'OK'; result={'schema_version':1,'artifact_type':'REQUIREMENT_WORKLIST_REGISTRATION_RESULT','requirement_worklist_registration_result':{'state':state,'added':added,'unchanged':unchanged,'review_required':review,'canonical_rq_created':False}}
 return canonical_doc,ledger_doc,result,(3 if review else 0)
def main():
 p=argparse.ArgumentParser(); p.add_argument('intake',type=Path); p.add_argument('--canonical',type=Path,required=True); p.add_argument('--ledger',type=Path,required=True); p.add_argument('--config',type=Path,required=True); p.add_argument('--result',type=Path); a=p.parse_args(); intake=load(a.intake); canonical=load(a.canonical) or {'schema_version':1,'artifact_type':'WORKLIST_CANONICAL','worklist_canonical':{'items':[]}}; ledger=load(a.ledger); cfg=load(a.config).get('registration') or load(a.config); canonical,ledger,result,rc=register(intake,canonical,ledger,cfg)
 if rc!=2: dump(a.canonical,canonical); dump(a.ledger,ledger)
 if a.result: dump(a.result,result)
 print(yaml.safe_dump(result,allow_unicode=True,sort_keys=False),end=''); return rc
if __name__=='__main__': raise SystemExit(main())
