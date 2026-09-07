#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

KOREAN_SECTIONS=['## 문서 목적','## 한눈에 보기','## 업무 흐름','## 입력 및 근거','## 상세 내용','## 미확정 사항·주의·가정','## 관련 ID 및 추적성','## 다음 작업']
FORBIDDEN_VISIBLE=['## Workflow','## 입력/Evidence','## 미확정/Alert/Assumption','## 관련 ID/Traceability']
CUSTOMER_REQUIRED=['문서 목적','한눈에 보기','고객과 함께 확인할 내용','합의된 내용','미확정 사항','다음 단계']
ACTIVE_CUSTOMER_TYPES=['solution_agreement','delivery_scope','acceptance_handover']


def validate(root: Path) -> list[str]:
    errors=[]
    semantic=root/'sdlc/templates/semantic'
    for p in semantic.glob('*.md'):
        txt=p.read_text(encoding='utf-8')
        for sec in KOREAN_SECTIONS:
            if sec not in txt: errors.append(f'{p.name}: missing Korean section {sec}')
        for sec in FORBIDDEN_VISIBLE:
            if sec in txt: errors.append(f'{p.name}: old mixed-language section remains {sec}')
    term=root/'sdlc/config/terminology-profile.example.json'
    cdoc=root/'sdlc/design/contracts/customer-document-contract.json'
    visibility=root/'sdlc/design/contracts/projection-visibility-contract.json'
    cprofile=root/'sdlc/config/customer-document-profile.json'
    brp=root/'sdlc/config/br-intake-profile.example.json'
    brs=root/'sdlc/design/contracts/br-candidate.schema.json'
    bre=root/'sdlc/design/contracts/br-document-extraction-contract.json'
    renderer=root/'sdlc/scripts/render_customer_document.py'
    runtime=root/'sdlc/scripts/customer_projection_runtime.py'
    for p in [term,cdoc,visibility,cprofile,brp,brs,bre,renderer,runtime]:
        if not p.exists(): errors.append(f'missing document-experience contract: {p.relative_to(root)}')
    if visibility.exists():
        v=json.loads(visibility.read_text(encoding='utf-8'))
        principles=v.get('principles',{})
        if not principles.get('allowlist_before_sanitize'):
            errors.append('projection visibility must select by allowlist before sanitize')
        if not principles.get('stable_block_ids_may_exist_as_hidden_markers'):
            errors.append('projection visibility must preserve hidden stable block markers')
        policy=v.get('customer_direct_canonical_policy',{})
        if policy.get('default') != 'ALLOWLIST_ONLY':
            errors.append('customer direct canonical visibility must be ALLOWLIST_ONLY')
        if policy.get('relation_expansion') != 'DENY_BY_DEFAULT':
            errors.append('customer direct canonical relation expansion must be denied by default')
    if cdoc.exists():
        c=json.loads(cdoc.read_text(encoding='utf-8'))
        for s in CUSTOMER_REQUIRED:
            if s not in c['required_base_sections']: errors.append(f'customer required section missing: {s}')
        active=c.get('active_document_types',[])
        if active != ACTIVE_CUSTOMER_TYPES:
            errors.append(f'active customer document types must be exactly {ACTIVE_CUSTOMER_TYPES}')
        stages=[]
        for dtype,spec in c['document_types'].items():
            stages += spec['stages']
            template=spec.get('template')
            if not template:
                errors.append(f'{dtype}: active customer template missing')
            else:
                path=root/'sdlc/templates/customer/standard'/template
                if not path.exists():
                    errors.append(f'{dtype}: customer template file missing: {template}')
                else:
                    txt=path.read_text(encoding='utf-8')
                    for section in CUSTOMER_REQUIRED:
                        if f'## {section}' not in txt:
                            errors.append(f'{template}: customer template missing required section {section}')
            if not spec.get('projection_sections'):
                errors.append(f'{dtype}: projection_sections missing')
        expected=['INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT','DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION']
        for stage in expected:
            if stage not in stages: errors.append(f'customer stage mapping missing: {stage}')
        aliases=c.get('legacy_document_aliases',{})
        if len(aliases) != 8:
            errors.append('legacy customer document aliases must preserve eight previous document type ids')
        for alias,target in aliases.items():
            if target not in active:
                errors.append(f'legacy customer alias target must be active: {alias}->{target}')
        projection=c.get('projection',{})
        if not projection.get('base_section_sources') or not projection.get('catalog_section_sources'):
            errors.append('customer projection mappings must define base and catalog section sources')
        if projection.get('direct_canonical_visibility') != 'ALLOWLIST_ONLY':
            errors.append('customer contract direct canonical visibility must be ALLOWLIST_ONLY')
        if projection.get('direct_relation_expansion') is not False:
            errors.append('customer contract must not expand Canonical relations into customer view by default')
        if projection.get('sanitizer_role') != 'SECONDARY_DEFENSE':
            errors.append('customer sanitizer must remain secondary defense after visibility selection')
        if projection.get('empty_section_policy') != 'EXPLICIT_NOT_FOUND':
            errors.append('customer projection must not invent content for empty source sections')
        # Legacy templates remain compatibility assets; all customer-facing files still keep the common base sections.
        for p in (root/'sdlc/templates/customer/standard').glob('*.md'):
            txt=p.read_text(encoding='utf-8')
            for s in CUSTOMER_REQUIRED:
                if f'## {s}' not in txt: errors.append(f'{p.name}: customer template missing required section {s}')
    if cprofile.exists():
        profile=json.loads(cprofile.read_text(encoding='utf-8'))
        if profile.get('active_document_types') != ACTIVE_CUSTOMER_TYPES:
            errors.append('customer profile must default to the three active customer views')
        display=profile.get('display',{})
        if display.get('show_internal_ids'):
            errors.append('customer profile must hide internal ids by default')
        if display.get('show_source_hash'):
            errors.append('customer profile must hide source hash by default')
        if display.get('show_confidence_status'):
            errors.append('customer profile must hide confidence status by default')
        overrides=profile.get('document_overrides',{})
        for dtype in ACTIVE_CUSTOMER_TYPES:
            disabled=set((overrides.get(dtype) or {}).get('disable_optional',[]))
            for appendix in ['기술_상세_부록','근거_상세_부록']:
                if appendix not in disabled:
                    errors.append(f'{dtype}: {appendix} must be disabled by default')
    if runtime.exists():
        txt=runtime.read_text(encoding='utf-8')
        for marker in [
            'CUSTOMER_CANONICAL_SAFE_FIELDS',
            'CUSTOMER_CANONICAL_DENIED_FIELDS',
            '_customer_safe_entity_fields',
            '_customer_safe_value',
            '"canonical_direct_input_visibility": "ALLOWLIST_ONLY"',
            '"canonical_relation_expansion": False',
        ]:
            if marker not in txt:
                errors.append(f'customer runtime visibility guard missing: {marker}')
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
