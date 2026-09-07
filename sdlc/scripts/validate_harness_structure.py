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
    core_required=set(c['core_required_files'])
    for rel in c['core_required_files']:
        if not (root/rel).is_file(): errors.append(f'missing core file: {rel}')

    if c.get('candidate_design') != 'v1.9.0-redteam-simplified':
        errors.append('active package contract must identify v1.9.0-redteam-simplified')
    for rel in ['sdlc/scripts/change_execution_runtime.py','sdlc/config/change-execution-policy.json']:
        if rel not in core_required:
            errors.append(f'change execution core dependency missing from package: {rel}')
    for group in ['official_entrypoint_required_files','default_tailoring_assets','default_user_guides']:
        required=c.get(group, [])
        if not isinstance(required, list) or not required:
            errors.append(f'package contract missing non-empty {group}')
            continue
        for rel in required:
            if rel not in core_required:
                errors.append(f'{group} item not in core_required_files: {rel}')
            if not (root/rel).is_file():
                errors.append(f'{group} file missing: {rel}')
    if 'sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml' in set(c.get('default_tailoring_assets', [])):
        errors.append('STAGE_ORIENTED_FULL must not be a new-project default Tailoring asset')
    if 'sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml' not in set(c.get('compatibility_tailoring_assets', [])):
        errors.append('STAGE_ORIENTED_FULL must remain available as compatibility asset')

    readiness_path=root/'sdlc/config/program-spec-readiness.json'
    if readiness_path.is_file():
        readiness=json.loads(readiness_path.read_text(encoding='utf-8'))
        package_rules=c.get('program_readiness_rules', {})
        if readiness.get('representation') != 'CORE_PLUS_RISK_TRIGGERED_CONDITIONAL':
            errors.append('program readiness must use CORE_PLUS_RISK_TRIGGERED_CONDITIONAL')
        if package_rules.get('representation') != readiness.get('representation'):
            errors.append('package/program readiness representation mismatch')
        if len(readiness.get('core_required_field_ids', [])) != int(package_rules.get('core_required_item_count', -1)):
            errors.append('package/program readiness core item count mismatch')
        legacy=len((readiness.get('legacy_compatibility') or {}).get('required_field_ids', []))
        if legacy != int(package_rules.get('legacy_full_item_count', -1)):
            errors.append('package/program readiness legacy item count mismatch')
    else:
        errors.append('program readiness config missing')

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
        rules=dev.get('rules', {})
        if not rules.get('not_applicable_requires_reason'):
            errors.append('developer spec N/A must require a reason')
        if not rules.get('functional_design_semantics_must_not_be_duplicated_in_program_spec'):
            errors.append('program spec must not duplicate functional design semantics')
        if not rules.get('all_program_delta_dimensions_are_not_unconditionally_required'):
            errors.append('program spec dimensions must not all be unconditionally required')
        if not rules.get('machine_derived_fields_are_not_human_maintenance'):
            errors.append('source-regeneratable program fields must not be human maintenance')
        ownership=dev.get('ownership_model', {})
        if ownership.get('functional_design') != 'SEMANTIC_SOURCE_OF_TRUTH':
            errors.append('functional design must be semantic source of truth')
        if ownership.get('program_spec') != 'IMPLEMENTATION_DELTA_AND_EXECUTION_READINESS':
            errors.append('program spec must be implementation delta and readiness')
        if not c['developer_specification'].get('legacy_program_dor_17_fields_preserved'):
            errors.append('legacy 17-field Program DoR must remain preserved for compatibility')
        if c['developer_specification'].get('legacy_program_dor_17_fields_default') is not False:
            errors.append('legacy 17-field Program DoR must not be the new-project default')

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
        required=set(oc.get('machine_required_item_fields', oc.get('required_item_fields', [])))
        for field in ['resolution_method','basis_class','decision_owner_role','resolution_status','downstream_impact']:
            if field not in required: errors.append(f'OPEN resolution machine item missing required field: {field}')
        states=set(oc.get('resolution_status', []))
        for state in ['PROPOSED','OBSERVED_AS_IS','ACCEPTED_DESIGN','CONFIRMED_BUSINESS','CONFLICT']:
            if state not in states: errors.append(f'OPEN resolution status missing: {state}')
        human=oc.get('human_view', {})
        if human.get('status_values') != ['미확정','확인중','제안','확정','보류']:
            errors.append('OPEN human view must use five simplified statuses')
        human_required=set(human.get('required_fields', []))
        for field in ['question_or_gap','resolution_action','current_or_proposed_value','decision_owner_role','human_status']:
            if field not in human_required: errors.append(f'OPEN human view missing required field: {field}')
    else:
        errors.append('open resolution contract missing')

    open_skill=root/open_cfg.get('skill','.cursor/skills/open-resolve/SKILL.md')
    if open_skill.is_file():
        txt=open_skill.read_text(encoding='utf-8')
        for marker in ['SOP는 유용한 Evidence이지만 필수 입력이 아니다','DESIGNER_PROPOSAL','DEVELOPER_PROPOSAL','OBSERVED_AS_IS','ACCEPTED_DESIGN','CONFIRMED_BUSINESS']:
            if marker not in txt: errors.append(f'OPEN resolution skill missing marker {marker}')
        for marker in ['미확정','확인중','제안','확정','보류']:
            if marker not in txt: errors.append(f'OPEN resolution skill missing human status {marker}')

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
