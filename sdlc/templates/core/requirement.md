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
  stage: INTAKE
sources: []
knowledge_used: []
generated_at: "{{generated_at}}"
---
# {{representative_id}} {{short_name}} 요구사항

## 문서 목적
{{purpose}}

## 30초 요약
{{summary}}

## Workflow
```mermaid
flowchart LR
    I["입력/Evidence"] --> A["분석"] --> O["현재 산출물"]
```

## 입력/Evidence
| 구분 | 값 | Truth/Evidence | Locator | Source Hash | Confidence | Status |
|---|---|---|---|---|---|---|
| 요구사항 | {{requirement_source}} | GIVEN | {{requirement_locator}} | - | HIGH | CURRENT |
| Source | {{source_summary}} | OBSERVED | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 본문
### 외부 요구사항 ID
{{external_requirement_id}}

### 현재 문제 또는 요청내용
{{current_problem}}

### 원하는 결과
{{desired_result}}

### 유지 조건
{{constraints}}

## 미확정/Alert/Assumption
{{alerts_and_assumptions}}

## 관련 ID/Traceability
{{traceability}}

## 다음 작업
{{next_step}}
