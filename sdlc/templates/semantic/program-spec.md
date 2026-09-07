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
<!-- 작성 안내: Functional Design의 업무/기능 의미를 반복하지 않는다. 실제 구현 Target과 구현 Delta만 기록한다. -->
<!-- Readiness 정책: Core Required 6개 + Typed Risk가 실제로 발생한 Conditional 항목만 작성한다. -->
<!-- L1/L2라고 AS-IS Source/Impact 분석을 생략하지 않는다. 다만 별도 Program 문서가 불필요하면 이 Template 자체를 생성하지 않을 수 있다. -->
<!-- LEGACY_FULL_17은 기존 계약 호환 전용이며 신규 프로젝트 기본값이 아니다. -->
<!-- Conditional trigger가 없는 행/단락은 N/A를 채우지 말고 최종 문서에서 제거한다. -->
<!-- Machine evidence mapping: 근거 위치=Locator / 원본 식별값=Source Hash / 신뢰 수준=Confidence / 현재 상태=Status -->
# {{representative_id}} {{short_name}} 프로그램 구현 명세

## 문서 목적
{{purpose}}

> 업무 시나리오, 화면/필드 의미, CRUD 의미, 업무 규칙과 업무 예외는 기능/요구 설계를 기준으로 한다. 이 문서는 Source에 실제로 구현할 위치와 차이, 검증에 필요한 기술 근거만 추가한다.

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    I["기능 의도·설계 기준"] --> T["실제 구현 대상"] --> M["구현 Delta"] --> S["Source 근거"] --> G["조건부 기술 위험"] --> D["개발·테스트"]
```

## 입력 및 근거
| 구분 | 내용 | 무엇을 근거로 판단했는가 | 근거 위치 | 원본 식별값 | 현재 상태 |
|---|---|---|---|---|---|
| 기능/요구 설계 기준 | {{functional_design_ref}} | 확정 업무/기능 의도 또는 승인 설계 | {{functional_design_locator}} | {{functional_design_hash}} | {{functional_design_status}} |
| 프로그램 소스/시스템 | {{source_summary}} | 현행 확인(OBSERVED) | {{source_locator}} | {{source_hash}} | {{source_status}} |
| 프로젝트 표준 | {{project_standard_summary}} | 프로젝트 표준 | {{project_standard_locator}} | {{project_standard_hash}} | {{project_standard_status}} |

## 상세 내용
### 기능 설계 기준점
- L3 이상 기능 설계 문서/버전: {{functional_design_ref}}
- L1/L2는 별도 Full 기능 설계 문서를 강제하지 않고 RQ Intent/AC 또는 승인된 설계 기준을 참조할 수 있다.
- 기능 요구사항(FR): {{fr_id}}
- 업무 시나리오(SCN): {{scenario_ids}}
- 이 프로그램이 담당하는 범위: {{functional_scope_ref}}
- 그대로 따르는 내용: {{inherited_functional_behavior}}
- 추가 확인이 필요한 내용: {{functional_design_open_refs}}

### 실제 구현 Target
- 프로그램(PGM): {{program_id}}
- 변경 유형: {{change_type}}
- 실행 유형: {{entry_point_kind}}
- 화면/API/배치/이벤트 진입점: {{entry_point_locator}}
- 애플리케이션 서비스: {{service_locator}}
- 저장소/매퍼/Client: {{repository_locator}}
- 실제 변경 대상 신뢰 수준: {{target_confidence}}
- 실제 Source가 아직 없으면: `OPEN_REAL_SOURCE`

#### 실제 파일·심볼 근거
| 파일/자산 | 클래스·메서드·심볼 | 근거 위치 | 원본 식별값 | 현재 상태 |
|---|---|---|---|---|
{{artifact_evidence_rows}}

### 구현 매핑과 차이
기능 설계에 정의된 의미를 다시 설명하지 말고 실제 구현 위치 또는 Delta만 적는다.

| 기능 설계 항목/ID | 구현 대상 | UI/DTO/API/DB 연결 | 구현 차이 또는 추가 제약 | 상태 |
|---|---|---|---|---|
{{implementation_mapping_rows}}

#### 입력/출력 기술 계약
<!-- CONDITIONAL: DATA_MAPPING_IMPACT. Trigger가 없으면 이 단락을 제거한다. -->
| 구분 | 기술 항목 | 자료형/형식 | 실제 연결 | 추가 검증/제약 | 상태 |
|---|---|---|---|---|---|
{{technical_io_contract_rows}}

### Query·Table·Source 구현 근거
<!-- MACHINE_DERIVED 우선. DATA_ACCESS_OR_SCHEMA_IMPACT가 없으면 상세 Query/Table을 사람이 유지하지 않는다. -->
- 실제 Mapper/Repository/Query: {{query_primary_assets}}
- 실제 Table/View/Column: {{actual_table_column}}
- WHERE/Join/Order/Group/Paging의 기능 설계 대비 구현 Delta: {{query_implementation_delta}}
- 권한/Data Scope Filter 구현: {{query_security_filter}}
- 성능 고려(Index/N+1/대량조회): {{query_performance}}
- SQL/Mapper/Schema 실제 근거 또는 Greenfield 승인 설계: {{query_evidence_or_candidate}}
- 공통코드/기준정보 실제 구현 위치: {{common_code_implementation}}

### 트랜잭션·실행 제어
<!-- CONDITIONAL: TRANSACTION_IMPACT 또는 CONCURRENCY_RISK. Trigger가 없으면 이 단락을 제거한다. -->
- 트랜잭션 범위: {{transaction}}
- 동시성/잠금: {{concurrency}}
- 중복 실행 방지: {{idempotency}}
- Retry/중복 요청 처리: {{retry_duplicate}}
- Scheduler/Feature Flag/Runtime Config: {{runtime_control}}

### 연계 구현 계약
<!-- CONDITIONAL: HAS_INTERFACE. Trigger가 없으면 이 단락을 제거한다. -->
| 대상 시스템/프로그램 | 실제 Protocol/Topic/API/File | 요청/응답 또는 Payload 연결 | Timeout/Retry | 실패 보관/재처리 | 상태 |
|---|---|---|---|---|---|
{{integration_implementation_rows}}

### 기술 제어와 운영 조건
<!-- CONDITIONAL: ERROR/SECURITY/OBSERVABILITY/NFR/ARCHITECTURE 관련 Typed Risk가 있는 항목만 남긴다. -->
- 기술 오류/Exception 연결: {{technical_exceptions}}
- 인증/인가 구현 위치: {{authorization_implementation}}
- 민감정보/마스킹: {{sensitive_data}}
- 감사 기록: {{audit}}
- 로그/지표/추적: {{observability}}
- SLA/처리량/운영 제약의 구현 반영: {{operational_constraints}}
- 적용 표준 및 예외: {{standards}}

### TASK·AC·TC·Source 연결
| 개발 작업(TASK) | 기능/인수조건 | 테스트(TC) | 변경 Source/자산 | 상태 |
|---|---|---|---|---|
{{delivery_trace_rows}}

### 구현 준비도
신규 프로젝트는 `Core Required + Risk-triggered Conditional` 정책을 사용한다. 아래 Core 6개는 항상 판단하고, Conditional 행은 해당 Typed Trigger가 있을 때만 최종 문서에 남긴다. 17개 전체 확인은 `LEGACY_FULL_17` 호환 Profile에서만 사용한다.

| 확인 항목 | 현재 상태(확정/미확정/비적용) | 근거 또는 미확정 이유 | 개발 영향 |
|---|---|---|---|
<!-- CORE REQUIRED -->
| 기능 설계 기준 | {{dor_functional_design_ref_status}} | {{dor_functional_design_ref_basis}} | {{dor_functional_design_ref_impact}} |
| 실제 구현 대상 | {{dor_implementation_target_status}} | {{dor_implementation_target_basis}} | {{dor_implementation_target_impact}} |
| 소스 근거 | {{dor_source_evidence_status}} | {{dor_source_evidence_basis}} | {{dor_source_evidence_impact}} |
| 개발 작업·변경 소스 | {{dor_task_source_status}} | {{dor_task_source_basis}} | {{dor_task_source_impact}} |
| 인수조건·테스트 연결 | {{dor_ac_tc_status}} | {{dor_ac_tc_basis}} | {{dor_ac_tc_impact}} |
| 남은 미확정·실행 가드 | {{dor_open_guard_status}} | {{dor_open_guard_basis}} | {{dor_open_guard_impact}} |
<!-- CONDITIONAL: DATA_MAPPING_IMPACT -->
| 입출력 구현 매핑 | {{dor_io_mapping_status}} | {{dor_io_mapping_basis}} | {{dor_io_mapping_impact}} |
<!-- CONDITIONAL: DATA_ACCESS_OR_SCHEMA_IMPACT -->
| 조회·저장 데이터 | {{dor_query_data_status}} | {{dor_query_data_basis}} | {{dor_query_data_impact}} |
<!-- CONDITIONAL: COMMON_CODE_IMPACT -->
| 공통코드·기준정보 | {{dor_common_code_status}} | {{dor_common_code_basis}} | {{dor_common_code_impact}} |
<!-- CONDITIONAL: TRANSACTION_IMPACT -->
| 트랜잭션 | {{dor_transaction_status}} | {{dor_transaction_basis}} | {{dor_transaction_impact}} |
<!-- CONDITIONAL: CONCURRENCY_RISK -->
| 동시성·중복 방지 | {{dor_concurrency_status}} | {{dor_concurrency_basis}} | {{dor_concurrency_impact}} |
<!-- CONDITIONAL: HAS_INTERFACE -->
| 연계 기술 계약 | {{dor_integration_status}} | {{dor_integration_basis}} | {{dor_integration_impact}} |
<!-- CONDITIONAL: ERROR_HANDLING_DELTA -->
| 오류·예외 처리 | {{dor_error_status}} | {{dor_error_basis}} | {{dor_error_impact}} |
<!-- CONDITIONAL: SECURITY_IMPACT -->
| 인증·인가·보안 | {{dor_security_status}} | {{dor_security_basis}} | {{dor_security_impact}} |
<!-- CONDITIONAL: OBSERVABILITY_IMPACT -->
| 감사·로그·관측 | {{dor_observability_status}} | {{dor_observability_basis}} | {{dor_observability_impact}} |
<!-- CONDITIONAL: NFR_OR_MIGRATION_IMPACT -->
| 성능·운영 조건 | {{dor_nfr_status}} | {{dor_nfr_basis}} | {{dor_nfr_impact}} |
<!-- CONDITIONAL: ARCHITECTURE_OR_STANDARD_IMPACT -->
| 적용 표준·예외 | {{dor_standards_status}} | {{dor_standards_basis}} | {{dor_standards_impact}} |

- 남은 구현 OPEN 수: {{dor_open_count}}
- 구현 준비 판정: {{readiness_verdict}}
- Source write Guard: {{execution_guard}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
