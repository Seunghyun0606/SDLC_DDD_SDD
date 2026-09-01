---
document_id: "{{document_id}}"
document_type: program_spec
requirement_id: "{{requirement_id}}"
version: "{{version}}"
status: "{{status}}"
quality: "{{quality}}"
validity: "{{validity}}"
generated_by:
  skill: work
  stage: PROGRAM
sources: []
knowledge_used: []
generated_at: "{{generated_at}}"
---
<!-- 작성 안내: 본문은 Agent 용어를 전제로 하지 않고 한국어 자연어로 작성한다. RQ/FR/BR/PGM/AC/TC 같은 코드는 첫 등장 시 한국어 명칭을 함께 적고 이후 추적용 식별자로 사용한다. -->
# {{representative_id}} {{short_name}} 프로그램 상세 설계

## 문서 목적
{{purpose}}

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    F["기능 요구사항과 기능 설계"] --> E["실제 소스 근거"] --> P["프로그램 상세 계약"] --> D["구현 준비도 점검"] --> T["개발 작업과 테스트 연결"]
```

## 입력 및 근거
| 구분 | 내용 | 사실/근거 구분 | 위치(Locator) | 원본 해시(Source Hash) | 신뢰도(Confidence) | 상태(Status) |
|---|---|---|---|---|---|---|
| 요구사항 | {{requirement_source}} | GIVEN | {{requirement_locator}} | - | HIGH | CURRENT |
| 프로그램 소스/시스템 근거 | {{source_summary}} | {{source_truth_type}} | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 상세 내용
### 프로그램 식별 및 추적
- 프로그램(PGM): {{program_id}}
- 기능 요구사항(FR): {{fr_id}}
- 외부 요구사항 ID: {{external_requirement_id}}
- 변경 유형: {{change_type}}
- 설계 상세 수준: {{spec_level}}
- 구현 준비 상태: {{implementation_readiness}}

### 진입점과 실제 변경 대상
- 실행 유형: {{entry_point_kind}}
- 화면/API/배치/연계 위치: {{entry_point_locator}}
- 애플리케이션 서비스: {{service_locator}}
- 저장소/매퍼: {{repository_locator}}
- 변경 대상 신뢰도: {{target_confidence}}

### 실제 파일·심볼 근거
| 파일/자산 | 클래스·메서드·심볼 | 위치(Locator) | 원본 해시(Source Hash) | 근거 상태 |
|---|---|---|---|---|
{{artifact_evidence_rows}}

### 입력 데이터 계약(DTO)
| 항목 | 자료형 | 필수 여부 | 근거 상태 | 검증 조건 |
|---|---|---|---|---|
{{input_contract_rows}}

### 출력 데이터 계약(DTO)
| 항목 | 자료형 | 근거 상태 | 의미 |
|---|---|---|---|
{{output_contract_rows}}

### 업무 검증·판단·상태 규칙
{{business_rules}}

### 데이터 저장 및 조회
- 논리 데이터: {{logical_data}}
- 실제 테이블/컬럼: {{actual_table_column}}
- 조회/저장/변경 방식: {{persistence_operation}}
- SQL/매퍼 근거: {{persistence_evidence}}
- 데이터 이행/보정 필요 여부: {{migration_backfill}}

### 트랜잭션·동시성·중복 처리
- 트랜잭션 범위: {{transaction}}
- 격리/잠금 방식: {{concurrency}}
- 중복 실행 방지: {{idempotency}}
- 재시도/중복 요청 처리: {{retry_duplicate}}

### 외부 시스템 연계 및 알림
- 연계 채널/시스템: {{integration_channel}}
- 메시지 구조: {{message_schema}}
- 타임아웃/재시도/실패보관: {{integration_resilience}}
- 데이터 매핑: {{payload_mapping}}

### 오류 및 예외 처리
{{exceptions}}

### 권한·보안·감사·관측성
- 권한 확인: {{authorization}}
- 민감정보/마스킹: {{sensitive_data}}
- 감사 기록: {{audit}}
- 로그/지표/추적: {{observability}}

### 성능 및 운영 조건
- 응답시간/SLA: {{sla}}
- 처리량/배치 시간대: {{volume}}
- 페이징/스트리밍: {{pagination}}
- 보관/복구: {{operations}}

### 적용 표준과 예외
{{standards}}

### 인수 조건(AC)과 테스트케이스(TC) 연결
{{ac_tc_mapping}}

### 개발 작업(TASK)과 변경 범위
{{development_tasks}}

### 구현 준비도(DoR) 점검
| 구현 전 확인 항목 | 상태 | 근거 또는 미확정 이유 |
|---|---|---|
{{dor_rows}}

- 미확정 항목 수: {{dor_open_count}}
- 구현 준비 판정: {{readiness_verdict}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
