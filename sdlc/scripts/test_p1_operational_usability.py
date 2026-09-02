#!/usr/bin/env python3
"""P1 operational usability self-test; no production-readiness claim."""
from __future__ import annotations
import subprocess, sys, tempfile
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'sdlc'/'scripts'; C=ROOT/'sdlc'/'config'; T=ROOT/'sdlc'/'templates'

def run(args, ok=(0,), cwd=ROOT):
    cp=subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True,check=False)
    if cp.returncode not in ok:
        raise AssertionError(f"rc={cp.returncode}: {' '.join(map(str,args))}\nstdout={cp.stdout}\nstderr={cp.stderr}")
    return cp

def main():
    authority=yaml.safe_load((C/'contract-authority.yaml').read_text(encoding='utf-8'))
    paths=[x['path'] for x in (authority.get('authorities') or {}).values()]
    assert len(paths)==len(set(paths))
    assert 'sdlc/design/validation' in authority.get('non_authoritative_roots',[])
    assert 'sdlc/guides' in authority.get('non_authoritative_roots',[])

    decisions=yaml.safe_load((C/'project-decisions.yaml').read_text(encoding='utf-8'))
    bootcfg=yaml.safe_load((C/'bootstrap-runtime.yaml').read_text(encoding='utf-8'))
    assert bootcfg.get('decision_authority')=='sdlc/config/project-decisions.yaml'
    greenfield=[k for k,v in decisions['decisions'].items() if 'GREENFIELD' in (v.get('applies_to') or [])]
    assert set(greenfield)==set(bootcfg.get('greenfield_decisions') or [])
    assert len(decisions.get('decisions') or {}) >= 16

    with tempfile.TemporaryDirectory() as td:
        d=Path(td)
        bootstrap=d/'bootstrap.yaml'; bootstrap.write_text('''project_bootstrap:\n  project_id: DEMO\n  resolved_mode: GREENFIELD\n  technology_decisions: []\n''',encoding='utf-8')
        registry=d/'decisions.yaml'
        run([sys.executable,S/'build_project_decision_registry.py',bootstrap,C/'project-decisions.yaml','-o',registry])
        run([sys.executable,S/'validate_project_decisions.py',registry,'--config',C/'project-decisions.yaml'])
        rd=yaml.safe_load(registry.read_text(encoding='utf-8'))['project_decisions']
        assert rd['decisions']['transaction_policy']['state']=='OPEN'
        assert any(x['action']=='source.write' for x in rd['action_blockers'])

        profile=d/'profile.yaml'; profile.write_text('project:\n  name: demo\n  mode: AUTO\nartifacts:\n  profile: STANDARD\nproviders:\n  registry: x.yaml\ncustomization:\n  overlays: []\n',encoding='utf-8')
        base='''overlay:\n  overlay_id: O1\n  scope: {project_id: DEMO}\n  state: ACTIVE\n  revision: 1\n  trigger: {type: PROJECT_STANDARD_REQUIRES_OVERRIDE, reason: customer standard}\n  basis: {truth_state: GIVEN, source_refs: [policy.md], evidence_ids: []}\n  safety: {copies_core_truth: false, sample_specific_only: false}\n  lifecycle: {activated_by: owner, activated_at: 2026-09-02T00:00:00Z}\n  change:\n'''
        good=d/'good.yaml'; good.write_text(base+'    target_key: artifacts.profile\n    core_or_profile_value: STANDARD\n    project_value: LITE\n',encoding='utf-8')
        bad=d/'bad.yaml'; bad.write_text(base.replace('O1','O2')+'    target_key: invented.magic\n    project_value: true\n',encoding='utf-8')
        stale=d/'stale.yaml'; stale.write_text(base.replace('O1','O3')+'    target_key: artifacts.profile\n    core_or_profile_value: ENTERPRISE\n    project_value: LITE\n',encoding='utf-8')
        out=d/'resolved.yaml'; run([sys.executable,S/'resolve_project_overlay.py',profile,good,'--schema',C/'overlay-schema.yaml','-o',out])
        assert yaml.safe_load(out.read_text(encoding='utf-8'))['resolved_project_configuration']['artifacts']['profile']=='LITE'
        run([sys.executable,S/'resolve_project_overlay.py',profile,bad,'--schema',C/'overlay-schema.yaml','-o',d/'badout.yaml'],ok=(2,))
        run([sys.executable,S/'resolve_project_overlay.py',profile,stale,'--schema',C/'overlay-schema.yaml','-o',d/'staleout.yaml'],ok=(2,))

        md=d/'work.md'; xlsx=d/'work.xlsx'; can=d/'canonical.yaml'; conflict=d/'conflicts.yaml'
        md.write_text('# 전체 작업 목록\n\n| 작업ID | 작업구분 | 작업명 | 단계 | 상태 | 변경버전 |\n|---|---|---|---|---|---|\n| TASK-1 | TASK | 최초 작업 | DESIGN | READY | 1 |\n',encoding='utf-8')
        run([sys.executable,S/'sync_worklist.py','--md',md,'--xlsx',xlsx,'--canonical',can,'--columns',C/'worklist-columns.yaml'])
        assert xlsx.exists() and can.exists()
        md.write_text(md.read_text(encoding='utf-8').replace('최초 작업','MD에서 다른 값'),encoding='utf-8')
        can_before=can.read_bytes(); xlsx_before=xlsx.read_bytes()
        run([sys.executable,S/'sync_worklist.py','--md',md,'--xlsx',xlsx,'--canonical',can,'--columns',C/'worklist-columns.yaml','--conflicts',conflict],ok=(3,))
        assert can.read_bytes()==can_before and xlsx.read_bytes()==xlsx_before
        assert yaml.safe_load(conflict.read_text(encoding='utf-8'))['conflicts'][0]['work_item_id']=='TASK-1'

        observed=d/'observed.yaml'; observed.write_text('''knowledge_candidate:\n  knowledge_id: K-BR-1\n  project_id: DEMO\n  type: BUSINESS_RULE\n  title: Rule\n  statement: observed behavior\n  truth_state: OBSERVED\n  promotion_state: CANDIDATE\n  revision: 1\n  provenance: {evidence_ids: [EV-1], source_refs: [], source_revision: abc}\n  review: {required: true, decision: CONFIRM, human_confirmation: false, reviewed_by: owner, reviewed_at: 2026-09-02T00:00:00Z, decision_basis: customer review}\n  relations: {supports: [], conflicts_with: [], supersedes: []}\n''',encoding='utf-8')
        kr=d/'knowledge-registry.yaml'
        run([sys.executable,S/'promote_knowledge.py',observed,'--config',C/'knowledge-promotion.yaml','--registry',kr],ok=(2,))
        confirmed=d/'confirmed.yaml'; confirmed.write_text(observed.read_text(encoding='utf-8').replace('human_confirmation: false','human_confirmation: true'),encoding='utf-8')
        run([sys.executable,S/'promote_knowledge.py',confirmed,'--config',C/'knowledge-promotion.yaml','--registry',kr])
        first=kr.read_bytes(); run([sys.executable,S/'promote_knowledge.py',confirmed,'--config',C/'knowledge-promotion.yaml','--registry',kr]); assert kr.read_bytes()==first
        entry=yaml.safe_load(kr.read_text(encoding='utf-8'))['knowledge_registry']['entries'][0]
        assert entry['truth_state']=='CONFIRMED' and entry['promotion_state']=='PROMOTED' and entry['canonical_publish_requested'] is False

    report={'schema_version':1,'artifact_type':'P1_OPERATIONAL_USABILITY_SELFTEST','state':'PASS','checks':{'contract_authority_unique':True,'decision_authority_and_compatibility_view_consistent':True,'project_decision_open_and_action_scope':True,'overlay_unknown_key_denied':True,'overlay_stale_base_denied':True,'worklist_md_xlsx_roundtrip':True,'same_revision_conflict_denied_without_overwrite':True,'knowledge_requires_explicit_human_confirmation':True,'knowledge_promotion_idempotent':True},'production_ready_claim_allowed':False,'reason':'real customer Source/Build/Test E2E remains an external production gate'}
    print(yaml.safe_dump(report,allow_unicode=True,sort_keys=False),end=''); return 0
if __name__=='__main__': raise SystemExit(main())
