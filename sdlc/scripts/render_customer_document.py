#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

BASE_PLACEHOLDERS={
    '문서 목적':'{{customer_purpose}}',
    '한눈에 보기':'{{customer_summary}}',
    '고객과 함께 확인할 내용':'{{customer_questions}}',
    '합의된 내용':'{{agreed_items}}',
    '미확정 사항':'{{open_items}}',
    '다음 단계':'{{next_steps}}',
}
STAGE_ORDER={name:i for i,name in enumerate([
    'INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT',
    'DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION'
])}
INTERNAL_ID_RE=re.compile(r'\b(?:RQ|FR|BR|PGM|TASK|AC|TC|SCN|PROC|ART|DATA|CODE|REQ)[:-]?[A-Z0-9_.-]+\b|\bREQ_[A-Z0-9_]+\b')
STATUS_TRANSLATIONS={
    'CONFIRMED_BUSINESS':'확정', 'ACCEPTED_DESIGN':'확정', 'PROPOSED':'제안',
    'CANDIDATE':'제안', 'ANALYZING':'확인중', 'DEFERRED':'보류',
    'OBSERVED_AS_IS':'현행 확인', 'N_A':'비적용'
}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def resolve_document_type(document_type: str, contract: dict) -> str:
    aliases=contract.get('legacy_document_aliases',{})
    resolved=aliases.get(document_type,document_type)
    if resolved not in contract['document_types']:
        raise KeyError(f'unknown customer document type: {document_type}')
    return resolved


def _document_override(requested_type: str, resolved_type: str, profile: dict) -> dict:
    overrides=profile.get('document_overrides',{})
    merged={"enable_optional":[],"disable_optional":[]}
    for key in [resolved_type,requested_type]:
        value=overrides.get(key,{})
        for name in value.get('enable_optional',[]):
            if name not in merged['enable_optional']:
                merged['enable_optional'].append(name)
        for name in value.get('disable_optional',[]):
            if name not in merged['disable_optional']:
                merged['disable_optional'].append(name)
    return merged


def enabled_optional(document_type: str, contract: dict, profile: dict) -> list[str]:
    resolved=resolve_document_type(document_type,contract)
    spec=contract['document_types'][resolved]
    enabled=[]
    for name in profile.get('default_optional_sections',[]):
        if name in contract['optional_section_catalog'] and name not in enabled:
            enabled.append(name)
    override=_document_override(document_type,resolved,profile)
    for name in override.get('enable_optional',[]):
        if name in contract['optional_section_catalog'] and name not in enabled:
            enabled.append(name)
    disabled=set(override.get('disable_optional',[]))
    required_add=set(spec.get('required_add',[]))
    return [x for x in enabled if x not in disabled and x not in required_add]


def _normalize_key(value: str) -> str:
    return re.sub(r'[^0-9a-zA-Z가-힣]+','',value).lower()


def _to_text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value,str):
        return value.strip()
    if isinstance(value,(int,float,bool)):
        return str(value)
    if isinstance(value,list):
        rows=[]
        for item in value:
            text=_to_text(item)
            if text:
                rows.append(text if text.startswith(('-', '*', '|')) else f'- {text}')
        return '\n'.join(rows)
    if isinstance(value,dict):
        rows=[]
        for key,item in value.items():
            text=_to_text(item)
            if text:
                rows.append(f'- {key}: {text}')
        return '\n'.join(rows)
    return str(value)


def parse_markdown_artifact(text: str, source: str='<memory>') -> dict:
    frontmatter=''
    body=text
    if text.startswith('---\n'):
        end=text.find('\n---\n',4)
        if end >= 0:
            frontmatter=text[4:end]
            body=text[end+5:]
    def meta(name: str) -> str | None:
        m=re.search(rf'^\s*{re.escape(name)}:\s*["\']?([^"\'\n]+)',frontmatter,re.M)
        return m.group(1).strip() if m else None
    title_match=re.search(r'^#\s+(.+?)\s*$',body,re.M)
    title=title_match.group(1).strip() if title_match else Path(source).stem
    headings=list(re.finditer(r'^(#{2,4})\s+(.+?)\s*$',body,re.M))
    sections={}
    for index,match in enumerate(headings):
        start=match.end()
        end=headings[index+1].start() if index+1 < len(headings) else len(body)
        name=match.group(2).strip()
        content=body[start:end].strip()
        if content:
            sections.setdefault(name,[]).append(content)
    return {
        'source':source,
        'artifact_type':meta('document_type'),
        'stage':meta('stage'),
        'title':title,
        'sections':sections,
        'fields':{}
    }


def _json_artifact_rows(data: Any, source: str) -> list[dict]:
    if isinstance(data,dict) and isinstance(data.get('artifacts'),list):
        rows=[]
        for idx,item in enumerate(data['artifacts']):
            rows.extend(_json_artifact_rows(item,f'{source}#artifacts[{idx}]'))
        return rows
    if not isinstance(data,dict):
        return []
    sections={}
    raw_sections=data.get('sections',{})
    if isinstance(raw_sections,dict):
        for key,value in raw_sections.items():
            text=_to_text(value)
            if text:
                sections.setdefault(str(key),[]).append(text)
    reserved={'artifacts','sections','artifact_type','document_type','stage','title','short_name','source'}
    fields={}
    for key,value in data.items():
        if key in reserved:
            continue
        text=_to_text(value)
        if text:
            fields[str(key)]=text
    return [{
        'source':data.get('source',source),
        'artifact_type':data.get('artifact_type') or data.get('document_type'),
        'stage':data.get('stage'),
        'title':data.get('title') or data.get('short_name') or Path(source).stem,
        'sections':sections,
        'fields':fields
    }]


def load_artifact_input(path: Path) -> list[dict]:
    if path.is_dir():
        rows=[]
        for child in sorted(path.rglob('*')):
            if child.is_file() and child.suffix.lower() in {'.md','.json'}:
                rows.extend(load_artifact_input(child))
        return rows
    if path.suffix.lower()=='.json':
        return _json_artifact_rows(load(path),str(path))
    return [parse_markdown_artifact(path.read_text(encoding='utf-8'),str(path))]


def _artifact_values(artifact: dict, candidate: str) -> list[str]:
    wanted=_normalize_key(candidate)
    exact=[]
    fuzzy=[]
    for container_name in ['sections','fields']:
        container=artifact.get(container_name,{})
        for key,value in container.items():
            key_norm=_normalize_key(str(key))
            values=value if isinstance(value,list) else [value]
            if key_norm==wanted:
                exact.extend(_to_text(v) for v in values if _to_text(v))
            elif wanted and (wanted in key_norm or key_norm in wanted):
                fuzzy.extend(_to_text(v) for v in values if _to_text(v))
    return exact or fuzzy


def sanitize_customer_text(text: str, contract: dict, profile: dict) -> str:
    if not text:
        return ''
    text=re.sub(r'<!--.*?-->','',text,flags=re.S)
    hidden=contract.get('projection',{}).get('customer_body_hidden_patterns',[])
    clean_lines=[]
    for line in text.splitlines():
        if any(pattern.lower() in line.lower() for pattern in hidden):
            continue
        clean_lines.append(line)
    text='\n'.join(clean_lines)
    if not profile.get('display',{}).get('show_internal_ids',False):
        text=INTERNAL_ID_RE.sub('',text)
    if not profile.get('display',{}).get('show_confidence_status',False):
        for source,target in STATUS_TRANSLATIONS.items():
            text=text.replace(source,target)
    if not profile.get('display',{}).get('show_source_hash',False):
        text=re.sub(r'\b(?:sha256:)?[0-9a-fA-F]{40,64}\b','',text)
    for source,target in profile.get('terminology_overrides',{}).items():
        text=text.replace(source,target)
    text=re.sub(r'[ \t]+\n','\n',text)
    text=re.sub(r'\n{3,}','\n\n',text)
    return text.strip(' \n-|')


def _eligible_artifacts(document_type: str, contract: dict, profile: dict, artifacts: list[dict]) -> list[dict]:
    resolved=resolve_document_type(document_type,contract)
    stages=set(contract['document_types'][resolved].get('stages',[]))
    rows=[a for a in artifacts if not a.get('stage') or a.get('stage') in stages]
    prefer_latest=profile.get('projection',{}).get('prefer_latest_stage_content',True)
    return sorted(rows,key=lambda a:STAGE_ORDER.get(a.get('stage'),-1),reverse=prefer_latest)


def _collect(candidates: list[str], artifacts: list[dict], contract: dict, profile: dict) -> str:
    values=[]
    seen=set()
    dedupe=profile.get('projection',{}).get('deduplicate_repeated_content',True)
    for candidate in candidates:
        for artifact in artifacts:
            for raw in _artifact_values(artifact,candidate):
                cleaned=sanitize_customer_text(raw,contract,profile)
                key=re.sub(r'\s+',' ',cleaned).strip().lower()
                if not cleaned or (dedupe and key in seen):
                    continue
                seen.add(key)
                values.append(cleaned)
    return '\n\n'.join(values)


def project(document_type: str, contract: dict, profile: dict, artifacts: list[dict], short_name: str | None=None) -> dict:
    resolved=resolve_document_type(document_type,contract)
    spec=contract['document_types'][resolved]
    eligible=_eligible_artifacts(document_type,contract,profile,artifacts)
    empty=contract.get('projection',{}).get('empty_section_text','현재 제공된 내부 산출물에서 확인되지 않았습니다.')
    projection={}
    projection['문서 목적']=f'내부 산출물을 바탕으로 {spec["title"]} 내용을 고객과 확인하고 공유하기 위한 문서입니다.'
    base_sources=contract.get('projection',{}).get('base_section_sources',{})
    for section in ['한눈에 보기','고객과 함께 확인할 내용','합의된 내용','미확정 사항','다음 단계']:
        content=_collect(base_sources.get(section,[section]),eligible,contract,profile)
        projection[section]=content or empty
    for section,candidates in spec.get('projection_sections',{}).items():
        projection[section]=_collect(candidates,eligible,contract,profile) or empty
    catalog_sources=contract.get('projection',{}).get('catalog_section_sources',{})
    for key in list(spec.get('required_add',[]))+enabled_optional(document_type,contract,profile):
        projection[key.replace('_',' ')]=_collect(catalog_sources.get(key,[key.replace('_',' ')]),eligible,contract,profile) or empty
    derived_name=short_name
    if not derived_name:
        for artifact in eligible:
            if artifact.get('title'):
                derived_name=artifact['title']
                break
    projection['_short_name']=derived_name or '프로젝트 변경'
    projection['_resolved_document_type']=resolved
    projection['_source_count']=len(eligible)
    return projection


def render(document_type: str, contract: dict, profile: dict, projection: dict | None=None) -> str:
    resolved=resolve_document_type(document_type,contract)
    spec=contract['document_types'][resolved]
    short_name=(projection or {}).get('_short_name','{{short_name}}')
    lines=[f'# {short_name} {spec["title"]}','',
           '<!-- 내부 Canonical/단계 산출물에서 파생되는 고객 커뮤니케이션 View. 새로운 업무 사실을 임의로 추가하지 않는다. -->','']

    def value(section: str, placeholder: str='{{content}}') -> str:
        if projection is None:
            return BASE_PLACEHOLDERS.get(section,placeholder)
        return projection.get(section,contract.get('projection',{}).get('empty_section_text',placeholder))

    for section in ['문서 목적','한눈에 보기']:
        lines += [f'## {section}',value(section),'']
    for section in spec.get('projection_sections',{}):
        lines += [f'## {section}',value(section),'']
    for key in spec.get('required_add',[]):
        section=key.replace('_',' ')
        lines += [f'## {section}',value(section),'']
    for section in ['고객과 함께 확인할 내용','합의된 내용','미확정 사항']:
        lines += [f'## {section}',value(section),'']
    for key in enabled_optional(document_type,contract,profile):
        section=key.replace('_',' ')
        lines += [f'## {section} (선택)',value(section,'{{optional_content}}'),'']
    lines += ['## 다음 단계',value('다음 단계'),'']
    if document_type != resolved:
        lines += [f'<!-- Legacy customer document type `{document_type}` → `{resolved}` 호환 변환 -->','']
    if not profile.get('display',{}).get('show_internal_ids',False):
        lines += ['<!-- 내부 RQ/FR/BR/PGM/TASK/AC/TC ID는 기본적으로 본문에 표시하지 않음 -->','']
    return '\n'.join(lines).rstrip()+"\n"


def main(argv=None):
    ap=argparse.ArgumentParser(description='내부 SDLC 산출물을 3개 표준 고객 View로 Projection한다.')
    ap.add_argument('--root',default='.')
    ap.add_argument('--type',required=True)
    ap.add_argument('--contract',default='sdlc/design/contracts/customer-document-contract.json')
    ap.add_argument('--profile',default='sdlc/config/customer-document-profile.example.json')
    ap.add_argument('--input',action='append',default=[],help='내부 Markdown/Canonical JSON 파일 또는 디렉터리. 반복 지정 가능')
    ap.add_argument('--short-name')
    ap.add_argument('--out')
    ns=ap.parse_args(argv)
    root=Path(ns.root)
    contract=load(root/ns.contract)
    profile=load(root/ns.profile)
    projection=None
    if ns.input:
        artifacts=[]
        for raw in ns.input:
            path=Path(raw)
            if not path.is_absolute():
                path=root/path
            artifacts.extend(load_artifact_input(path))
        projection=project(ns.type,contract,profile,artifacts,ns.short_name)
    text=render(ns.type,contract,profile,projection)
    if ns.out:
        p=Path(ns.out)
        if not p.is_absolute():
            p=root/p
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text,encoding='utf-8')
    else:
        print(text,end='')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
