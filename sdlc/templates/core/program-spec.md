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
<!-- 작성 안내: 기존 17개 Program DoR를 유지하면서 개발자가 구현할 수 있는 화면/필드/CRUD/로직/쿼리/테이블/공통코드/연계 상세를 추가한다. OPEN은 숨기지 않고, N/A는 사유를 적는다. -->
# {{representative_id}} {{short_name}} 프로그램 상세 설계

## 문서 목적
{{purpose}}

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    S["6하원칙 업무 시나리오"] --> F["기능 설계"] --> E["실제 소스/프로젝트 근거"] --> P["개발 상세 계약"] --> D["DoR·개발 상세 완성도"] --> T["TASK·AC·TC"]
```

## 입력 및 근거
| 구분 | 내용 | 사실/근거 구분 | 위치(Locator) | 원본 해시(Source Hash) | 신뢰도(Confidence) | 상태(Status) |
|---|---|---|---|---|---|---|
| 요구사항 | {{requirement_source}} | GIVEN | {{requirement_locator}} | - | HIGH | CURRENT |
| 업무/SOP 근거 | {{business_source_summary}} | {{business_truth_type}} | {{business_source_locator}} | {{business_source_hash}} | {{business_source_confidence}} | {{business_source_status}} |
| 프로그램 소스/시스템 근거 | {{source_summary}} | {{source_truth_type}} | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 상세 내용
### 프로그램 식별 및 추적
- 프로그램(PGM): {{program_id}}
- 기능 요구사항(FR): {{fr_id}}
- 업무 시나리오(SCN): {{scenario_ids}}
- 외부 요구사항 ID: {{external_requirement_id}}
- 변경 유형: {{change_type}}
- 설계 상세 수준: {{spec_level}}
- 구현 준비 상태: {{implementation_readiness}}

### 업무 시나리오(6하원칙) 연결
| 시나리오 ID | 누가(Who) | 언제(When) | 어디서(Where) | 무엇을(What) | 어떻게(How) | 왜(Why) | PGM 구현 책임 |
|---|---|---|---|---|---|---|---|
{{six_w_program_rows}}

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

### 화면·메뉴·컴포넌트 상세
- 화면 적용 여부: {{ui_applicability}}
- 메뉴 경로/화면 ID: {{menu_screen_id}}
- 진입 권한/프로파일: {{screen_authorization}}
- 선행/후속 화면: {{screen_navigation}}
- N/A 사유: {{ui_not_applicable_reason}}

| 영역/컴포넌트 ID | 유형 | 표시 내용 | 행위 | 표시/활성 조건 | 이벤트/연결 PGM |
|---|---|---|---|---|---|
{{ui_component_rows}}

### 화면·입력·출력 필드 상세
| 필드 ID | 업무 명칭 | UI 컴포넌트 | DTO 필드 | 자료형/길이/형식 | 필수 | 기본값 | 코드그룹 | Validation | 권한/표시 조건 | DB/API 매핑 |
|---|---|---|---|---|---|---|---|---|---|---|
{{field_detail_rows}}

### CRUD 동작 매트릭스
| 행위/버튼/이벤트 | C | R | U | D | 대상 객체 | 호출 진입점 | 주요 Validation | 트랜잭션 | 성공 결과 | 실패 결과 |
|---|---|---|---|---|---|---|---|---|---|---|
{{crud_detail_rows}}

### 입력 데이터 계약(DTO)
| 항목 | 자료형 | 필수 여부 | 근거 상태 | 검증 조건 |
|---|---|---|---|---|
{{input_contract_rows}}

### 출력 데이터 계약(DTO)
| 항목 | 자료형 | 근거 상태 | 의미 |
|---|---|---|---|
{{output_contract_rows}}

### 핵심 비즈니스 로직 실행 순서
1. {{logic_step_1}}
2. {{logic_step_2}}
3. {{logic_step_3}}
{{additional_logic_steps}}

#### 조건·판단·계산 규칙
| 순번/우선순위 | 조건 | 입력 데이터 | 판단/계산 | 상태 변화/결과 | 오류/예외 | 근거 상태 |
|---|---|---|---|---|---|---|
{{business_logic_rows}}

### 업무 검증·판단·상태 규칙
{{business_rules}}

### 조회 쿼리·데이터 접근 상세
- 조회 목적: {{query_purpose}}
- 기준 테이블/뷰/매퍼/Repository: {{query_primary_assets}}
- 조회 조건(WHERE): {{query_conditions}}
- 조인 관계: {{query_joins}}
- 정렬(ORDER BY): {{query_order}}
- 집계/GROUP BY: {{query_aggregation}}
- 페이징/Limit: {{query_paging}}
- 권한/데이터 범위 Filter: {{query_security_filter}}
- 성능 고려(Index/N+1/대량조회): {{query_performance}}
- SQL/Mapper 실제 근거 또는 Greenfield 후보: {{query_evidence_or_candidate}}

### 데이터 저장 및 조회
- 논리 데이터: {{logical_data}}
- 실제 테이블/컬럼: {{actual_table_column}}
- 조회/저장/변경 방식: {{persistence_operation}}
- SQL/매퍼 근거: {{persistence_evidence}}
- 데이터 이행/보정 필요 여부: {{migration_backfill}}

### 공통코드·기준정보 사용
| 코드 그룹/기준정보 | 코드/값 | 의미 | 사용 필드/로직 | 조회 방식 | 유효기간/조건 | 실제 근거/상태 |
|---|---|---|---|---|---|---|
{{common_code_rows}}

### 트랜잭션·동시성·중복 처리
- 트랜잭션 범위: {{transaction}}
- 격리/잠금 방식: {{concurrency}}
- 중복 실행 방지: {{idempotency}}
- 재시도/중복 요청 처리: {{retry_duplicate}}

### 연계 프로그램·외부 시스템 상세
| 대상 프로그램/시스템 | 방향 | 호출/이벤트 조건 | Protocol/Topic/API/File | 요청/응답 데이터 | 동기/비동기 | Timeout/Retry | 실패 보관/재처리 | 필요 여부/근거 |
|---|---|---|---|---|---|---|---|---|
{{integration_detail_rows}}

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

### 개발 상세 명세 완성도
| 항목 | 상태(RESOLVED/OPEN/N/A) | 실제 근거 또는 N/A 사유 | 개발 영향 |
|---|---|---|---|
{{developer_spec_completeness_rows}}

- OPEN 상세 명세 수: {{developer_spec_open_count}}
- 개발 상세 명세 판정: {{developer_spec_verdict}}

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
