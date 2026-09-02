#!/usr/bin/env python3
"""P2 integrated scale-out self-test using existing real workbook evidence and generic synthetic source fixtures."""
from __future__ import annotations
import copy, sys, tempfile
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]; SCRIPTS=ROOT/'sdlc/scripts'; sys.path.insert(0,str(SCRIPTS))
from analyze_batch_scheduler import analyze
from register_requirement_worklist import register
from assess_scaleout_readiness import assess
def load(rel): return yaml.safe_load((ROOT/rel).read_text(encoding='utf-8')) or {}
def test_batch_scheduler_observation_only():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td); (root/'cronjob.yaml').write_text('''apiVersion: batch/v1\nkind: CronJob\nmetadata:\n  name: nightly\nspec:\n  schedule: "0 2 * * *"\n  jobTemplate:\n    spec:\n      template:\n        spec:\n          containers:\n          - name: run\n            image: app:1\n''',encoding='utf-8'); (root/'Job.java').write_text('@Scheduled(cron="0 */10 * * * *") public void run(){}\n@EnableBatchProcessing class Batch{}',encoding='utf-8')
  out=analyze(root,['cronjob.yaml','Job.java'])['source_analysis_result']; kinds={o['kind'] for e in out['evidence'] for o in e['objects']}; assert {'KUBERNETES_CRONJOB','SPRING_SCHEDULED','SPRING_BATCH_SIGNAL'}<=kinds; assert all(e['truth_state']=='OBSERVED' and e['business_truth_confirmed'] is False for e in out['evidence'])
def test_real_requirement_intake_registers_noncanonical_work_item():
 intake=load('sdlc/design/validation/p2-representative-brownfield-slice-v1/requirements-intake-REQ_TM_TE100.yaml'); cfg=load('sdlc/config/requirement-worklist-registration.yaml')['registration']; can={'schema_version':1,'artifact_type':'WORKLIST_CANONICAL','worklist_canonical':{'items':[]}}; led={}
 can,led,res,rc=register(intake,can,led,cfg); assert rc==0; item=can['worklist_canonical']['items'][0]; assert item['requirement_id']=='REQ_TM_TE100' and item['item_type']=='SOURCE_REQUIREMENT' and item['validity']=='CANDIDATE'; assert res['requirement_worklist_registration_result']['canonical_rq_created'] is False; assert 'row=141' in item['note']
 can2,led2,res2,rc2=register(intake,can,led,cfg); assert rc2==0 and res2['requirement_worklist_registration_result']['unchanged']==['SRCREQ-REQ_TM_TE100']
 changed=copy.deepcopy(intake); changed['requirement_intake']['records'][0]['requirement_text']='changed'; can3,led3,res3,rc3=register(changed,can2,led2,cfg); assert rc3==3 and res3['requirement_worklist_registration_result']['review_required'][0]['code']=='SOURCE_REQUIREMENT_CHANGED_REVIEW_REQUIRED'; assert can3['worklist_canonical']['items'][0]['revision']=='1'
def test_analyzer_registry_complete_for_p2():
 cfg=load('sdlc/config/source-analyzers.yaml'); states={x['analyzer_id']:x['state'] for x in cfg['registry']['analyzers']}; assert states['interface-contract']=='AVAILABLE' and states['batch-scheduler']=='AVAILABLE'
def test_evidence_based_scaleout_keeps_production_false_without_customer_e2e():
 p0=load('sdlc/design/validation/p0-production-readiness-v1/p0-status.yaml'); p1=load('sdlc/design/validation/p1-usability-authority-v1/p1-status.yaml'); an=load('sdlc/config/source-analyzers.yaml'); cfg=load('sdlc/config/p2-scaleout-readiness.yaml')['scaleout_readiness']; out=assess(p0,p1,an,cfg,None,ROOT)['scaleout_readiness']; assert out['controlled_pilot_scaleout_ready'] is True; assert out['production_scaleout_ready'] is False; assert out['state']=='CONTROLLED_PILOT_SCALEOUT_READY_EXTERNAL_E2E_REQUIRED'; assert 'REAL_CUSTOMER_E2E_EVIDENCE_REQUIRED' in out['external_blockers']
def main():
 tests=[test_batch_scheduler_observation_only,test_real_requirement_intake_registers_noncanonical_work_item,test_analyzer_registry_complete_for_p2,test_evidence_based_scaleout_keeps_production_false_without_customer_e2e]
 for t in tests: t(); print('PASS',t.__name__)
 print(f'PASS P2 integrated scale-out tests={len(tests)}'); return 0
if __name__=='__main__': raise SystemExit(main())
