#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

BASE_PLACEHOLDERS={
    '문서 목적':'{{customer_purpose}}',
    '한눈에 보기':'{{customer_summary}}',
    '고객과 함께 확인할 내용':'{{customer_questions}}',
    '합의된 내용':'{{agreed_items}}',
    '미확정 사항':'{{open_items}}',
    '다음 단계':'{{next_steps}}',
}

def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def enabled_optional(document_type: str, contract: dict, profile: dict) -> list[str]:
    spec=contract['document_types'][document_type]
    enabled=[]
    for name in profile.get('default_optional_sections',[]):
        if name in contract['optional_section_catalog'] and name not in enabled:
            enabled.append(name)
    override=profile.get('document_overrides',{}).get(document_type,{})
    for name in override.get('enable_optional',[]):
        if name in contract['optional_section_catalog'] and name not in enabled:
            enabled.append(name)
    disabled=set(override.get('disable_optional',[]))
    required_add=set(spec.get('required_add',[]))
    return [x for x in enabled if x not in disabled and x not in required_add]

def render(document_type: str, contract: dict, profile: dict) -> str:
    if document_type not in contract['document_types']:
        raise KeyError(f'unknown customer document type: {document_type}')
    spec=contract['document_types'][document_type]
    lines=[f'# {{{{short_name}}}} {spec["title"]}','',
           '<!-- 내부 Canonical/단계 산출물에서 파생되는 고객 커뮤니케이션 View. 새로운 업무 사실을 임의로 추가하지 않는다. -->','']
    for section in contract['required_base_sections']:
        lines += [f'## {section}',BASE_PLACEHOLDERS.get(section,'{{content}}'),'']
    for key in spec.get('required_add',[]):
        lines += [f'## {key.replace("_"," ")}','{{content}}','']
    for key in enabled_optional(document_type,contract,profile):
        lines += [f'## {key.replace("_"," ")} (선택)','{{optional_content}}','']
    if not profile.get('display',{}).get('show_internal_ids',False):
        lines += ['<!-- 내부 RQ/FR/BR/PGM/TASK/AC/TC ID는 기본적으로 본문에 표시하지 않음 -->','']
    return '\n'.join(lines).rstrip()+"\n"

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ap.add_argument('--type',required=True)
    ap.add_argument('--contract',default='sdlc/design/contracts/customer-document-contract.json')
    ap.add_argument('--profile',default='sdlc/config/customer-document-profile.example.json')
    ap.add_argument('--out')
    ns=ap.parse_args(argv)
    root=Path(ns.root)
    text=render(ns.type,load(root/ns.contract),load(root/ns.profile))
    if ns.out:
        p=root/ns.out; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    else:
        print(text,end='')
    return 0
if __name__=='__main__': raise SystemExit(main())
