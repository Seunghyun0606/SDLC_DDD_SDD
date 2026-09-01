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
        if tp.is_file():
            txt=tp.read_text(encoding='utf-8')
            for sec in c['template_required_sections']:
                if sec not in txt: errors.append(f'{stage}: template missing section {sec}')
            if spec.get('source_evidence'):
                for marker in c['source_evidence_markers']:
                    if marker not in txt: errors.append(f'{stage}: source-enabled template missing {marker}')
    core=(root/'.cursor/rules/00-core.mdc').read_text(encoding='utf-8') if (root/'.cursor/rules/00-core.mdc').exists() else ''
    for marker in c['core_invariant_markers']:
        if marker not in core: errors.append(f'core invariant marker missing: {marker}')
    sp=(root/'sdlc/config/source-profile.example.yaml').read_text(encoding='utf-8') if (root/'sdlc/config/source-profile.example.yaml').exists() else ''
    for marker in ['static_analysis_first: true','full_repository_llm_scan: false','preserve_source_hash: true','ambiguous_write: DEFERRED_TARGET_DECISION','dangerous_action_policy: EXECUTION_GUARD']:
        if marker not in sp: errors.append(f'source profile contract missing: {marker}')
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
