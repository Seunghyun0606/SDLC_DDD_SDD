#!/usr/bin/env python3
"""Evidence-based P2 scale-out readiness assessment; production readiness cannot be asserted by CLI flags."""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import yaml
def load(p:Path)->dict[str,Any]: return yaml.safe_load(p.read_text(encoding='utf-8')) or {}
def nested(doc,*keys):
 cur=doc
 for k in keys:
  if not isinstance(cur,dict): return None
  cur=cur.get(k)
 return cur
def assess(p0,p1,analyzers,config,customer=None,repo_root:Path|None=None):
 blockers=[]; p0state=nested(p0,'status','implementation_state') or nested(p0,'status','state'); p1state=nested(p1,'status','implementation_state')
 if p0state not in set(config.get('accepted_p0_states') or []): blockers.append('P0_ENGINEERING_NOT_COMPLETE')
 if p1state not in set(config.get('accepted_p1_states') or []): blockers.append('P1_ENGINEERING_NOT_COMPLETE')
 available={x.get('analyzer_id') for x in (nested(analyzers,'registry','analyzers') or []) if x.get('state')=='AVAILABLE'}
 for x in sorted(set(config.get('required_available_analyzers') or [])-available): blockers.append(f'ANALYZER_UNAVAILABLE:{x}')
 if repo_root is not None:
  for rel in config.get('required_runtime_paths') or []:
   if not (repo_root/rel).is_file(): blockers.append(f'RUNTIME_PATH_MISSING:{rel}')
 controlled=not blockers; external=[]; production=False
 if customer is None: external.append('REAL_CUSTOMER_E2E_EVIDENCE_REQUIRED')
 else:
  root=customer.get('customer_e2e_evidence') or customer.get('status') or customer
  checks={'real_customer_source_validated':root.get('real_customer_source_validated') is True,'actual_test_runtime_validated':root.get('actual_test_runtime_validated') is True,'reverse_sync_reviewed':root.get('reverse_sync_reviewed') is True,'production_verified':root.get('production_verified') is True}
  external += [k.upper()+'_REQUIRED' for k,v in checks.items() if not v]
  if not (root.get('evidence_refs') or []): external.append('CUSTOMER_EVIDENCE_REFS_REQUIRED')
  production=controlled and not external
 state='PRODUCTION_SCALEOUT_READY' if production else ('CONTROLLED_PILOT_SCALEOUT_READY_EXTERNAL_E2E_REQUIRED' if controlled else 'ACTION_REQUIRED')
 return {'schema_version':1,'artifact_type':'P2_SCALEOUT_READINESS','scaleout_readiness':{'state':state,'controlled_pilot_scaleout_ready':controlled,'production_scaleout_ready':production,'engineering_blockers':blockers,'external_blockers':external,'truth_guards':{'production_readiness_cannot_be_asserted_by_cli_flag':True,'missing_customer_e2e_is_not_success':True}}}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--p0-status',type=Path,required=True); p.add_argument('--p1-status',type=Path,required=True); p.add_argument('--analyzers',type=Path,required=True); p.add_argument('--config',type=Path,required=True); p.add_argument('--customer-e2e',type=Path); p.add_argument('--repo-root',type=Path,default=Path('.')); p.add_argument('-o','--output',type=Path); a=p.parse_args(); cfg=load(a.config); result=assess(load(a.p0_status),load(a.p1_status),load(a.analyzers),cfg.get('scaleout_readiness') or cfg,load(a.customer_e2e) if a.customer_e2e else None,a.repo_root.resolve()); text=yaml.safe_dump(result,allow_unicode=True,sort_keys=False)
 if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding='utf-8')
 else: print(text,end='')
 return 0 if result['scaleout_readiness']['controlled_pilot_scaleout_ready'] else 2
if __name__=='__main__': raise SystemExit(main())
