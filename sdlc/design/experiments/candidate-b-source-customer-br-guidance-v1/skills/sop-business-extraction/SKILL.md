# SoP Business Evidence Extraction Skill

## Purpose

PPT/XLSX/Word/PDF 기반 업무 SoP/정책/매뉴얼/요구사항에서 **6W + BR/FR/UI/Data/Integration Evidence Candidate**를 추출하고, 각 항목의 provenance/authority/scope/effective/revision을 유지한다.

출력은 K1/Confirmed BR가 아니라 `Business Evidence Package`다.

## Pre-Prompt

1. 원문에 없는 6W 값을 생성하지 말고 `OPEN`으로 둔다.
2. 모든 추출값은 정확한 locator를 가져야 한다.
3. 문서의 현재 화면/Source 설명과 공식 업무정책을 구분한다.
4. Authority와 Effective Period가 불명확한 Rule은 Promotion하지 않는다.
5. 문서 간 충돌은 해결하지 말고 `CONFLICTING_EVIDENCE`로 남긴다.
6. High-blast Rule은 Human scope/temporal confirmation 전 K1 금지.
7. Extraction 완료(`progress=COMPLETE`)와 Knowledge Promotion 가능 여부를 분리한다.

## Format Rules

### XLS/XLSX
- sheet/header hierarchy
- row/cell/range provenance
- merged-cell parent context
- ID/업무분류/요구문구
- Role/Profile, 주기/Trigger, Menu/Program, Field/Object
- CRUD/승인/마감/전송 등 Action
- 조건/예외/상태/공통코드
- Program/Table/Interface 언급
- formula 존재 여부

한 행을 자동 RQ/BR로 Publish하지 않는다.

### PPT/PPTX
- slide title/section
- text/table/process shape
- arrow/decision node
- screenshot의 field/button은 VISUAL_CANDIDATE
- notes는 별도 evidence family
- AS-IS/TO-BE

### DOCX/PDF
- heading/page/section/table/footnote
- 정책형 문장
- 적용대상/기간
- Role/Approval
- revision/approval history

## Output Item

```yaml
item:
  provenance:
    source_id: BSRC-0012
    locator: "slide=12/table=1/row=3"
    raw_text: "..."
  source_authority: A3_PROJECT_AGREED
  six_w:
    who: {value: null, truth: OPEN, evidence: []}
    when: {value: null, truth: OPEN, evidence: []}
    where: {value: null, truth: OPEN, evidence: []}
    what: {value: null, truth: OPEN, evidence: []}
    how: {value: null, truth: OPEN, evidence: []}
    why: {value: null, truth: OPEN, evidence: []}
  candidates:
    rq: []
    fr: []
    br: []
    ui: []
    data: []
    integration: []
    common_code: []
  promotion:
    br_confirm: DENY_UNTIL_AUTHORITY_SCOPE_EFFECTIVE
    k1: DENY_UNTIL_HUMAN_CONFIRMATION_IF_HIGH_BLAST
```

## Question Priority

1. Why/Business Goal
2. Who/권한
3. When/Trigger/상태
4. Where/채널/메뉴
5. What/입출력 Object/Field
6. How/Validation/Exception/Integration
7. Scope/Authority/Effective

## Action Permissions

Extraction 단계에서 허용:
- evidence extraction: ALLOW
- BR candidate: ALLOW
- RQ/FR candidate: ALLOW
- customer review view: ALLOW

제한:
- canonical BR confirm: REQUIRES_AUTHORITY_SCOPE
- high-blast K1 promotion: REQUIRES_HUMAN
- source_write: NOT_GRANTED_BY_EXTRACTION

## Do Not

- PPT/XLSX 문구를 그대로 K1 Truth로 승격하지 않는다.
- screenshot에서 숨은 권한/validation을 추측하지 않는다.
- source locator 없는 Evidence를 만들지 않는다.
- 최신/구형 문서 충돌을 timestamp만으로 자동 해결하지 않는다.
