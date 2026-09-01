#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

KOREAN_SECTIONS=['## 문서 목적','## 한눈에 보기','## 업무 흐름','## 입력 및 근거','## 상세 내용','## 미확정 사항·주의·가정','## 관련 ID 및 추적성','## 다음 작업']
FORBIDDEN_VISIBLE=['## Workflow','## 입력/Evidence','## 미확정/Alert/Assumption','## 관련 ID/Traceability']
CUSTOMER_REQUIRED=['문서 목적','한눈에 보기','고객과 함께 확인할 내용','합의된 내용','미확정 사항','다음 단계']

def validate(root: Path) -> list[str]:
    errors=[]
    core=root/'sdlc/templates/core'
    for p in core.glob('*.md'):
        txt=p.read_text(encoding='utf-8')
        for sec in KOREAN_SECTIONS:
            if sec not in txt: errors.append(f'{p.name}: missing Korean section {sec}')
        for sec in FORBIDDEN_VISIBLE:
            if sec in txt: errors.append(f'{p.name}: old mixed-language section remains {sec}')
    term=root/'sdlc/config/terminology-profile.example.json'
    cdoc=root/'sdlc/design/contracts/customer-document-contract.json'
    cprofile=root/'sdlc/config/customer-document-profile.example.json'
    brp=root/'sdlc/config/br-intake-profile.example.json'
    brs=root/'sdlc/design/contracts/br-candidate.schema.json'
    bre=root/'sdlc/design/contracts/br-document-extraction-contract.json'
    for p in [term,cdoc,cprofile,brp,brs,bre]:
        if not p.exists(): errors.append(f'missing document-experience contract: {p.relative_to(root)}')
    if cdoc.exists():
        c=json.loads(cdoc.read_text(encoding='utf-8'))
        for s in CUSTOMER_REQUIRED:
            if s not in c['required_base_sections']: errors.append(f'customer required section missing: {s}')
        stages=[]
        for spec in c['document_types'].values(): stages += spec['stages']
        expected=['INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT','DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION']
        for stage in expected:
            if stage not in stages: errors.append(f'customer stage mapping missing: {stage}')
        for p in (root/'sdlc/templates/customer/standard').glob('*.md'):
            txt=p.read_text(encoding='utf-8')
            for s in CUSTOMER_REQUIRED:
                if f'## {s}' not in txt: errors.append(f'{p.name}: customer template missing required section {s}')
    if brp.exists():
        b=json.loads(brp.read_text(encoding='utf-8'))
        if b.get('minimum_manifest_fields') != ['document_id','path']: errors.append('BR minimum manifest must remain document_id + path')
        if not b.get('preserve_original_files'): errors.append('BR originals must be preserved')
    if brs.exists():
        s=json.loads(brs.read_text(encoding='utf-8'))
        ev=s['properties']['source_evidence']
        if ev.get('minItems') != 1: errors.append('BR candidate requires source evidence')
        for f in ['document_id','locator','source_hash','confidence']:
            if f not in ev['items']['required']: errors.append(f'BR evidence required field missing: {f}')
    if bre.exists():
        e=json.loads(bre.read_text(encoding='utf-8'))
        for f in ['document_id','locator','raw_text','source_hash','extraction_status','extraction_method']:
            if f not in e.get('required_output_fields',[]): errors.append(f'BR extraction output field missing: {f}')
        if 'EXTRACTION_REQUIRED' not in e.get('extraction_status',[]): errors.append('BR extraction status missing EXTRACTION_REQUIRED')
    return errors

def main(argv=None):
    args=argv or sys.argv[1:]
    root=Path(args[0] if args else '.')
    errors=validate(root)
    if errors:
        for e in errors: print('ERROR:',e,file=sys.stderr)
        return 1
    print('Document experience contract OK')
    return 0
if __name__=='__main__': raise SystemExit(main())
