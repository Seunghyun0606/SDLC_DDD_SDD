---
document_id: "{{document_id}}"
document_type: requirement
requirement_id: "{{requirement_id}}"
version: "{{version}}"
status: "{{status}}"
quality: "{{quality}}"
validity: "{{validity}}"
generated_by:
  skill: work
  stage: DECOMPOSE
sources: []
knowledge_used: []
generated_at: "{{generated_at}}"
---
<!-- 작성 안내: 요구 원문/외부 ID와 분석 결과를 한 문서에서 관리한다. INTAKE용 별도 문서와 DECOMPOSE용 분석 문서를 중복 생성하지 않는다. -->
# {{representative_id}} {{short_name}} 요구사항 정의

## 문서 목적
요구 원문과 외부 ID를 보존하면서, 개발·테스트 가능한 기능 요구사항(FR)과 인수 조건(AC), 업무 규칙 후보를 한 곳에서 정의한다.

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    I["요구 원문/외부 ID"] --> N["요청·목표 정리"] --> F["기능 요구사항 분해"] --> A["인수 조건"] --> O["미확정 이월"]
```

## 입력 및 근거
| 구분 | 내용 | 사실/근거 구분 | 위치(Locator) | 원본 해시(Source Hash) | 신뢰도(Confidence) | 상태(Status) |
|---|---|---|---|---|---|---|
| 요구사항 원문 | {{requirement_source}} | GIVEN | {{requirement_locator}} | {{requirement_source_hash}} | HIGH | CURRENT |
| 고객/업무 보충자료 | {{business_source_summary}} | {{business_truth_type}} | {{business_source_locator}} | {{business_source_hash}} | {{business_source_confidence}} | {{business_source_status}} |
| 기존 시스템/Source 근거 | {{source_summary}} | OBSERVED | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 상세 내용
### 원문과 식별정보
- 외부 요구사항 ID: {{external_requirement_id}}
- 원문: {{original_text}}
- 정규화 문장: {{normalized_text}}
- 요청자/출처: {{request_source}}

### 현재 문제 또는 요청 내용
{{current_problem}}

### 업무 목표와 기대 결과
- 업무 목표: {{business_goal}}
- 기대 결과: {{desired_result}}

### 범위와 반드시 유지할 조건
- 포함 범위: {{scope_in}}
- 제외 범위: {{scope_out}}
- 제약/유지 조건: {{constraints}}

### 기능 요구사항(FR)
각 FR은 하나의 테스트 가능한 행동 단위로 만든다.

| 기능 요구사항(FR) ID | 사용자가/시스템이 해야 할 일 | 근거 | 상태 |
|---|---|---|---|
{{fr_rows}}

### 업무 규칙(BR) 후보
아직 업무 권한자가 확정하지 않은 규칙은 후보 또는 OPEN으로 유지한다.

{{business_rule_candidates}}

### 인수 조건(AC)
| 인수 조건(AC) ID | 확인할 결과 | 관련 FR | 상태 |
|---|---|---|---|
{{acceptance_criteria_rows}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
