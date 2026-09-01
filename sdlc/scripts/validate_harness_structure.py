#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path


def validate(root: Path) -> list[str]:
    errors=[]
    contract_path=root/'sdlc/design/contracts/harness-package-contract.json'
    if not contract_path.exists():
        return ['missing contract: sdlc/design/contracts/harness-package-contract.json']
    c=json.loads(contract_path.read_text(encoding='utf-8'))
    for rel in c['core_required_files']:
        if not (root/rel).is_file(): errors.append(f'missing core file: {rel}')
    for d in c['customization_roots']:
        if not (root/d).is_dir(): errors.append(f'missing customization root: {d}')
    profile=(root/'sdlc/config/project-profile.example.yaml').read_text(encoding='utf-8')
    last=-1
    for item in c['overlay_precedence']:
        pos=profile.find(f'- {item}')
        if pos<0: errors.append(f'overlay missing from project profile: {item}')
        elif pos<=last: errors.append(f'overlay order invalid at: {item}')
        last=max(last,pos)

    agent_contract_path=root/c['agent_execution']['contract']
    agent_contract=json.loads(agent_contract_path.read_text(encoding='utf-8')) if agent_contract_path.is_file() else {}
    execution_markers=agent_contract.get('execution_contract_required_markers', [])

    refs=root/'.cursor/skills/work/references'
    templates=root/'sdlc/templates/core'
    for stage,spec in c['stage_contracts'].items():
        rp=refs/spec['reference']; tp=templates/spec['template']
        if not rp.is_file(): errors.append(f'{stage}: missing reference {spec["reference"]}')
        if not tp.is_file(): errors.append(f'{stage}: missing template {spec["template"]}')
        if rp.is_file():
            txt=rp.read_text(encoding='utf-8')
            for sec in c['work_reference_required_sections']:
                if sec not in txt: errors.append(f'{stage}: reference missing section {sec}')
            for marker in execution_markers:
                if marker not in txt: errors.append(f'{stage}: execution contract missing marker {marker}')
        if tp.is_file():
            txt=tp.read_text(encoding='utf-8')
            for sec in c['template_required_sections']:
                if sec not in txt: errors.append(f'{stage}: template missing section {sec}')
            if spec.get('source_evidence'):
                for marker in c['source_evidence_markers']:
                    if marker not in txt: errors.append(f'{stage}: source-enabled template missing {marker}')
            if stage == 'PROCESS':
                for marker in c.get('process_sixw_required_markers', []):
                    if marker not in txt: errors.append(f'{stage}: six-w marker missing {marker}')
            if stage == 'DESIGN':
                for marker in c.get('functional_design_required_markers', []):
                    if marker not in txt: errors.append(f'{stage}: developer design marker missing {marker}')
            if stage == 'PROGRAM':
                for marker in c.get('program_spec_required_markers', []):
                    if marker not in txt: errors.append(f'{stage}: program detail marker missing {marker}')

    sixw_path=root/c['business_scenario']['contract']
    if sixw_path.is_file():
        sixw=json.loads(sixw_path.read_text(encoding='utf-8'))
        dims=sixw.get('required_dimensions', [])
        if [x.get('id') for x in dims] != ['who','when','where','what','how','why']:
            errors.append('business scenario contract must define who/when/where/what/how/why in order')
        if not sixw.get('rules', {}).get('missing_dimension_must_be_open_not_invented'):
            errors.append('business scenario missing dimension must remain OPEN')

    dev_path=root/c['developer_specification']['contract']
    if dev_path.is_file():
        dev=json.loads(dev_path.read_text(encoding='utf-8'))
        if not dev.get('rules', {}).get('not_applicable_requires_reason'):
            errors.append('developer spec N/A must require a reason')
        if not c['developer_specification'].get('legacy_program_dor_17_fields_preserved'):
            errors.append('legacy 17-field Program DoR must remain preserved')

    open_cfg=c.get('open_resolution', {})
    open_path=root/open_cfg.get('contract','sdlc/design/contracts/open-resolution-contract.json')
    if open_path.is_file():
        oc=json.loads(open_path.read_text(encoding='utf-8'))
        principles=oc.get('principles', {})
        if not principles.get('open_is_actionable_design_backlog'):
            errors.append('OPEN must be an actionable design backlog')
        if not principles.get('sop_is_optional') or not principles.get('missing_sop_does_not_block_design'):
            errors.append('SOP must remain optional for OPEN resolution')
        if not principles.get('proposal_is_not_automatic_business_truth'):
            errors.append('designer/developer proposal must not become business truth automatically')
        if not principles.get('existing_system_observation_is_not_automatic_target_policy'):
            errors.append('AS-IS observation must not become TO-BE policy automatically')
        required=set(oc.get('required_item_fields', []))
        for field in ['resolution_method','basis_class','decision_owner_role','resolution_status','downstream_impact']:
            if field not in required: errors.append(f'OPEN resolution item missing required field: {field}')
        states=set(oc.get('resolution_status', []))
        for state in ['PROPOSED','OBSERVED_AS_IS','ACCEPTED_DESIGN','CONFIRMED_BUSINESS','CONFLICT']:
            if state not in states: errors.append(f'OPEN resolution status missing: {state}')
    else:
        errors.append('open resolution contract missing')

    open_skill=root/open_cfg.get('skill','.cursor/skills/open-resolve/SKILL.md')
    if open_skill.is_file():
        txt=open_skill.read_text(encoding='utf-8')
        for marker in ['SOP는 유용한 Evidence이지만 필수 입력이 아니다','DESIGNER_PROPOSAL','DEVELOPER_PROPOSAL','OBSERVED_AS_IS','ACCEPTED_DESIGN','CONFIRMED_BUSINESS']:
            if marker not in txt: errors.append(f'OPEN resolution skill missing marker {marker}')

    if 'open_resolution:' not in profile or 'sop_required: false' not in profile:
        errors.append('project profile must configure non-blocking OPEN resolution')

    sop_path=root/c['sop_extraction']['skill']
    if sop_path.is_file():
        sop=sop_path.read_text(encoding='utf-8')
        for marker in ['누가(Who)','언제(When)','어디서(Where)','무엇을(What)','어떻게(How)','왜(Why)','Business Rule Candidate','structured_content']:
            if marker not in sop: errors.append(f'SOP extraction skill missing marker {marker}')

    core=(root/'.cursor/rules/00-core.mdc').read_text(encoding='utf-8') if (root/'.cursor/rules/00-core.mdc').exists() else ''
    for marker in c['core_invariant_markers']:
        if marker not in core: errors.append(f'core invariant marker missing: {marker}')
    sp=(root/'sdlc/config/source-profile.example.yaml').read_text(encoding='utf-8') if (root/'sdlc/config/source-profile.example.yaml').exists() else ''
    for marker in ['static_analysis_first: true','full_repository_llm_scan: false','preserve_source_hash: true','ambiguous_write: DEFERRED_TARGET_DECISION','dangerous_action_policy: EXECUTION_GUARD']:
        if marker not in sp: errors.append(f'source profile contract missing: {marker}')

    impact_path=root/c['brownfield_impact']['contract']
    if impact_path.is_file():
        impact=json.loads(impact_path.read_text(encoding='utf-8'))
        boundary=impact.get('project_adapter_boundary', {})
        if not boundary.get('adapter_required_for_project_specific_resolution'):
            errors.append('brownfield impact must require project-specific relation adapter')
        if not boundary.get('core_does_not_implement_language_framework_specific_resolution'):
            errors.append('brownfield impact must preserve core/project implementation boundary')
        if not impact.get('core_responsibility', {}).get('coverage_gaps_must_be_reported'):
            errors.append('brownfield impact coverage gaps must be reported')

    drift_path=root/c['source_drift_reverse']['contract']
    if drift_path.is_file():
        drift=json.loads(drift_path.read_text(encoding='utf-8'))
        rules=drift.get('rules', {})
        if rules.get('auto_rewrite_artifact') is not False:
            errors.append('source drift must not auto rewrite artifacts')
        if rules.get('auto_update_business_truth') is not False:
            errors.append('source drift must not auto update business truth')
    return errors


def main(argv=None):
    argv=argv or sys.argv[1:]
    root=Path(argv[0] if argv else '.')
    errors=validate(root)
    if errors:
        for e in errors: print('ERROR:',e,file=sys.stderr)
        return 1
    print('Harness structure contract OK')
    return 0

if __name__=='__main__': raise SystemExit(main())
