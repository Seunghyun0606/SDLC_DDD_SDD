---
document_id: "{{document_id}}"
document_type: functional_design
requirement_id: "{{requirement_id}}"
version: "{{version}}"
status: "{{status}}"
quality: "{{quality}}"
validity: "{{validity}}"
generated_by:
  skill: work
  stage: DESIGN
sources: []
knowledge_used: []
generated_at: "{{generated_at}}"
---
# {{representative_id}} {{short_name}} 기능설계

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
### Evidence 기반 AS-IS
{{evidence_based_as_is}}

### TO-BE 정상 흐름
{{to_be_flow}}

### Input / Output / Validation
{{io_validation}}

### State / Exception
{{state_exception}}

### Data / Transaction / Authorization / Interface
{{technical_behavior}}

### Logging / Audit / NFR
{{nfr}}

### AC Mapping
{{ac_mapping}}

## 미확정/Alert/Assumption
{{alerts_and_assumptions}}

## 관련 ID/Traceability
{{traceability}}

## 다음 작업
{{next_step}}
