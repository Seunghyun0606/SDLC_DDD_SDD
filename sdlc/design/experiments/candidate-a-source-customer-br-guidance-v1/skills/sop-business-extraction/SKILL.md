# SoP Business Extraction Skill

## Purpose

고객/프로젝트의 비정형 업무 SoP(Standard Operating Procedure), 정책서, 매뉴얼, 요구사항서, PPT/XLSX/Word/PDF에서 **6W 업무 시나리오 + BR/FR/UI/Data/Integration 후보**를 일관된 Template으로 추출한다.

이 Skill의 출력은 `CONFIRMED BR`가 아니라 **Provenance를 가진 Extraction Package / Candidate**다.

## Required Input

- 원본 문서 또는 추출 가능한 내용
- `source_id`
- 파일명/형식
- 가능하면 source metadata: 문서유형, 작성부서, 승인상태, 적용조직, 시행일

## Pre-Prompt / Extraction Instruction

다음 원칙을 항상 적용한다.

1. 원문에 없는 내용을 관행/상식으로 채우지 말고 `OPEN`으로 둔다.
2. 추출한 모든 항목에 원문 위치를 기록한다.
   - XLSX: `sheet + row/cell/range`
   - PPT: `slide + shape/table/notes`
   - DOCX/PDF: `heading/section + page/table`
3. 화면 설명과 업무 Rule을 구분한다. 현재 화면 동작이 곧 Business Truth라는 가정을 금지한다.
4. 회의록/메모의 발언은 공식 정책과 구분한다.
5. 표의 Header, 병합 Cell, 각주, 예외행을 함께 해석하고 문맥을 잃지 않는다.
6. 6W 중 누락된 항목을 자동 생성하지 않고 Clarification Question으로 변환한다.
7. 최종 BR로 승격하기 전에 scope/authority/effective period를 별도로 확인한다.

## Format-specific Extraction

### XLS/XLSX

우선 추출:

- Sheet 역할/업무영역
- Header hierarchy
- Legacy ID / Requirement ID
- Actor/Role/Profile 관련 Column
- 주기/일자/시점/Trigger
- Menu/화면/프로그램/Batch/API
- 업무대상/입력필드/출력필드
- CRUD 표현(조회/등록/수정/삭제/승인/마감/전송)
- 조건/예외/상태/코드
- 인터페이스/연계 대상
- Table/Data/Program이 명시된 경우 후보로 추출

주의:

- 한 행을 자동으로 하나의 RQ/BR로 간주하지 않는다.
- 병합 Cell의 상위 분류를 각 상세행 Provenance에 유지한다.
- 수식 Cell은 표시값과 수식 존재 여부를 분리 기록한다.

### PPT/PPTX

우선 추출:

- Slide title / section
- Process diagram의 Actor/Step/Decision/Arrow
- Screen capture의 메뉴/Field/버튼(Visual Candidate)
- Table의 Rule/Condition/Exception
- Speaker notes가 있으면 별도 Evidence
- AS-IS / TO-BE 비교

주의:

- Screenshot만으로 숨은 Validation/권한을 추정하지 않는다.
- 화살표/도형 연결은 Process Candidate이며 업무 Rule Confirm이 아니다.

### DOC/DOCX/PDF

우선 추출:

- Heading/Section hierarchy
- 규정 문장(해야 한다/할 수 없다/예외)
- 적용대상/적용기간
- 절차/Role/승인주체
- 표/각주/부록
- Revision/Approval table

## Extraction Schema

각 업무 단위를 다음으로 출력한다.

```yaml
sop_item:
  source:
    source_id: BSRC-0012
    locator: "Sheet=근무계획!A15:I18"
    raw_excerpt: "..."
  classification:
    source_type: REQUIREMENT
    authority: A3_PROJECT_AGREED
  six_w:
    who:
      role: null
      auth_profile: null
      truth: OPEN
    when:
      trigger: "매일"
      truth: OBSERVED
    where:
      channel: ESS
      menu: 탄력근로제 근무계획
      truth: OBSERVED
    what:
      object: 근무계획
      fields: [근무일자, 시작시간, 종료시간]
      truth: OBSERVED
    how:
      action: 저장
      crud: CREATE_OR_UPDATE_CANDIDATE
      truth: OBSERVED
    why:
      purpose: null
      truth: OPEN
  candidates:
    rq: []
    fr: []
    br: []
    ui: []
    data: []
    integration: []
    common_code: []
  questions: []
```

## Candidate Generation Rules

### BR Candidate
BR 후보는 원문에서 Condition/Result/Exception의 형태가 발견될 때만 만든다.

### FR Candidate
사용자가 수행하거나 시스템이 제공해야 하는 독립 행동을 후보로 만든다.

### UI Candidate
메뉴/화면/필드/버튼이 명시되거나 Screen capture에서 관찰될 때 생성한다. 이미지에서 의미를 추론한 값은 `VISUAL_CANDIDATE`로 표시한다.

### Data / Query Candidate
Table/Column/조회조건이 원문에 있으면 추출하되 Source Repository로 확인 전 `CANDIDATE`다.

### Integration Candidate
API/인터페이스/전자결재/Batch/송수신/파일 등 명시적 연계 표현이 있으면 생성한다.

## Clarification Question Generation

우선순위:

1. Why / Business Goal
2. Who / 권한주체
3. When / Trigger와 상태
4. Where / 실제 실행 채널
5. What / 입력·출력 대상
6. How / Validation·예외·승인·연계

질문은 문서에 이미 답이 있으면 생성하지 않는다.

## Output

- `sop-extraction.yaml`
- `business-definition-6w.md` Candidate
- RQ/FR/BR Candidate links
- `clarification.md`
- Source provenance index

## Do Not

- 원본 PPT/XLSX를 직접 Canonical BR로 Publish하지 않는다.
- Screen 동작을 공식 Policy로 승격하지 않는다.
- 구형 매뉴얼과 최신 정책 충돌을 자동 해결하지 않는다.
- 6W 결측을 LLM 추론으로 숨기지 않는다.
- Source 위치 없는 Rule Candidate를 만들지 않는다.
