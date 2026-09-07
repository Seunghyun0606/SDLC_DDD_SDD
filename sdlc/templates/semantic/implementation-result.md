---
document_id: "{{document_id}}"
document_type: implementation_result
requirement_id: "{{requirement_id}}"
version: "{{version}}"
status: "{{status}}"
quality: "{{quality}}"
validity: "{{validity}}"
generated_by:
  skill: work
  stage: DEVELOPMENT
sources: []
knowledge_used: []
generated_at: "{{generated_at}}"
---
<!-- 작성 안내: 본문은 Agent 용어를 전제로 하지 않고 한국어 자연어로 작성한다. RQ/FR/BR/PGM/AC/TC 같은 코드는 첫 등장 시 한국어 명칭을 함께 적고 이후 추적용 식별자로 사용한다. -->
# {{representative_id}} {{short_name}} 구현 결과

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
### 변경된 프로그램 소스 근거
| 파일 | 클래스·메서드·심볼 | 변경 전 해시 | 변경 후 해시 | 개발 작업(TASK) |
|---|---|---|---|---|
{{changed_source_rows}}

### 구현 결과 요약
{{implementation_summary}}

### 설계와 달라진 부분
{{design_deviation}}

### 빌드 및 정적 점검 결과
{{build_evidence}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
