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
<!-- 작성 안내: 본문은 Agent 용어를 전제로 하지 않고 한국어 자연어로 작성한다. RQ/FR/BR/PGM/AC/TC 같은 코드는 첫 등장 시 한국어 명칭을 함께 적고 이후 추적용 식별자로 사용한다. -->
# {{representative_id}} {{short_name}} 요구사항 정리

## 문서 목적
{{purpose}}

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    I["입력 자료와 근거"] --> A["분석 및 확인"] --> O["현재 단계 산출물"]
```

## 입력 및 근거
| 구분 | 내용 | 사실/근거 구분 | 위치(Locator) | 원본 해시(Source Hash) | 신뢰도(Confidence) | 상태(Status) |
|---|---|---|---|---|---|---|
| 요구사항 | {{requirement_source}} | GIVEN | {{requirement_locator}} | - | HIGH | CURRENT |
| 프로그램 소스/시스템 근거 | {{source_summary}} | OBSERVED | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 상세 내용
### 외부 요구사항 ID
{{external_requirement_id}}

### 현재 문제 또는 요청 내용
{{current_problem}}

### 기대하는 결과
{{desired_result}}

### 반드시 유지해야 할 조건과 범위
{{constraints}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
