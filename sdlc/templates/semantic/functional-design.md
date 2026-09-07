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
<!-- 작성 안내: 개발자가 이 문서만으로 사용자 동작, 화면/필드, CRUD, 핵심 규칙, 데이터/연계, 권한, 예외와 미확정 항목을 이해할 수 있어야 한다. 미확정은 OPEN, 비적용은 사유와 함께 N/A로 기록한다. -->
<!-- Machine evidence mapping: 근거 위치=Locator / 원본 식별값=Source Hash / 확인 수준=Confidence / 현재 상태=Status -->
# {{representative_id}} {{short_name}} 기능 설계

## 문서 목적
{{purpose}}

## 한눈에 보기
{{summary}}

## 업무 흐름
```mermaid
flowchart LR
    B["6하원칙 업무 정의"] --> U["사용자/시스템 행위"] --> R["업무 규칙·CRUD"] --> D["데이터·연계"] --> A["인수 조건"]
```

## 입력 및 근거
| 구분 | 내용 | 무엇을 근거로 판단했는가 | 근거 위치 | 원본 식별값 | 확인 수준 | 현재 상태 |
|---|---|---|---|---|---|---|
| 요구사항 | {{requirement_source}} | 요청/제공 근거(GIVEN) | {{requirement_locator}} | - | 높음 | 현재 사용 |
| 업무/SOP 근거 | {{business_source_summary}} | {{business_truth_type}} | {{business_source_locator}} | {{business_source_hash}} | {{business_source_confidence}} | {{business_source_status}} |
| 프로그램 소스/시스템 근거 | {{source_summary}} | 현행 확인(OBSERVED) | {{source_locator}} | {{source_hash}} | {{source_confidence}} | {{source_status}} |

## 상세 내용
### 업무 정의(6하원칙)
| 시나리오 ID | 누가 | 언제 | 어디서 | 무엇을 | 어떻게 | 왜 | 현재 확인 상태/근거 |
|---|---|---|---|---|---|---|---|
{{six_w_scenario_rows}}

**자연어 업무 정의**  
{{six_w_natural_statement}}

### 근거로 확인된 현재(AS-IS) 동작
{{evidence_based_as_is}}

### 개선(TO-BE) 후 정상 업무 흐름
{{to_be_flow}}

### 화면·채널 및 사용자 동선
- 진입 유형: {{entry_point_kind}}
- 시스템/채널: {{channel_system}}
- 메뉴/화면/API/배치/이벤트 위치: {{entry_surface}}
- 선행 화면/후속 화면 또는 호출 흐름: {{navigation_flow}}
- 화면 비적용 시 사유: {{ui_not_applicable_reason}}

#### 화면 구성 초안
| 영역/컴포넌트 | 목적 | 노출 조건 | 사용자 행위 | 비고 |
|---|---|---|---|---|
{{ui_component_rows}}

### 화면·입력·출력 필드 명세
| 필드 ID | 화면/업무 명칭 | 입출력 | 자료형/형식 | 필수 | 기본값 | 코드/도메인 | 검증 규칙 | 표시/활성 조건 | 저장/조회 대상 |
|---|---|---|---|---|---|---|---|---|---|
{{field_catalog_rows}}

### CRUD 및 사용자/시스템 행위
| 기능/행위 | 생성 | 조회 | 변경 | 삭제 | 수행 주체 | 선행 조건 | 결과/후속 처리 |
|---|---|---|---|---|---|---|---|
{{crud_matrix_rows}}

### 핵심 업무 로직과 판단 규칙
#### 처리 순서
{{core_logic_steps}}

#### 판단 규칙
| 우선순위 | 조건 | 판단/계산 | 처리 결과 | 예외/메시지 | 현재 확인 상태 |
|---|---|---|---|---|---|
{{decision_rule_rows}}

### 데이터 조회·저장 설계
- 주요 업무 데이터: {{logical_data}}
- 조회 조건: {{query_conditions}}
- 정렬/페이징/집계: {{query_sort_paging_aggregation}}
- 조인/연관 데이터 후보: {{query_relationships}}
- 저장/변경/삭제 정책: {{persistence_behavior}}
- Brownfield 실제 테이블/컬럼 근거: {{actual_table_column_evidence}}
- Greenfield 데이터 모델 후보: {{target_data_model_candidate}}

### 공통코드·기준정보
| 코드 그룹/기준정보 | 사용 목적 | 코드/값 | 표시명 | 유효/필터 조건 | 근거/상태 |
|---|---|---|---|---|---|
{{common_code_rows}}

### 연계 프로그램·외부 시스템
| 연계 대상 | 방향 | 실행 시점 | 입력/출력 | 동기/비동기 | 실패/재처리 | 필요 여부/근거 |
|---|---|---|---|---|---|---|
{{integration_rows}}

### 권한·상태·예외
- 역할/프로파일별 권한: {{authorization}}
- 상태 전이: {{state_transition}}
- 입력 검증/업무 예외: {{validation_and_exception}}
- 오류 메시지/사용자 안내: {{user_error_message}}

### 로그·감사·비기능 요구사항
{{nfr}}

### 인수 조건(AC) 연결
{{ac_mapping}}

### 개발 상세 명세 준비도
| 확인 항목 | 현재 상태(확정/미확정/비적용) | 근거 또는 비적용 사유 |
|---|---|---|
{{developer_spec_readiness_rows}}

## 미확정 사항·주의·가정
{{alerts_and_assumptions}}

## 관련 ID 및 추적성
{{traceability}}

## 다음 작업
{{next_step}}
