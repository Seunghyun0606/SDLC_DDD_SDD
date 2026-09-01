# P2 Representative Brownfield Slice Contract v1

상태: `ACTIVE_P2_CANDIDATE`

## 목적

P0/P1 Safety Contract와 Structural Redesign v1을 유지한 상태에서 실제 고객형 Requirement Workbook을 직접 Intake하고, 하나의 대표 Source Requirement가 Brownfield Runtime 경계를 안전하게 통과하는지 검증한다.

이번 P2는 Production 구현 완료를 의미하지 않는다. 실제 고객 Source Provider가 연결되지 않은 상태에서 Source/Interface 구조를 추측하지 않고 정확히 `ACTION_REQUIRED`로 남기는 것까지가 대표 Slice의 성공 조건이다.

## 실제 Requirement Source

검증 입력은 제공된 `요구사항목록.xlsx`다.

- SHA-256: `d7dd76d786e97b66435bf4b9dc03fe04b8d55c580b565f2d45817893349ba39f`
- Worksheet: `Sheet1`
- Header Row: 2
- Requirement Source Rows: 142
- Duplicate Requirement ID: 0
- 필수값 누락으로 Skip된 Row: 0

대표 Slice:

- Source Requirement ID: `REQ_TM_TE100`
- Workbook Row: `141`
- Level1: `근태관리`
- Level2: `Interface`
- 요구사항명: `10분단위 근무계획 개선 Yellow Page 송신 반영을 구현`
- 요구사항: `구성원 근무계획 Yellow Page 송신`

Workbook 값은 `GIVEN`이며 Canonical RQ/FR이 아니다.

## P2 Runtime Pipeline

```text
XLSX
→ Requirement Intake
→ Source Requirement
→ Stage Input Pack
→ Artifact Profile
→ Stage Routing
→ Command Context
→ Provider Capability Routing
→ Generic E2E Read Model
```

실제 Source가 연결된 이후에는 다음이 이어진다.

```text
Bounded Inventory
→ Explicit Target Files
→ Java/Spring / SQL / Domain Adapter
→ Observed Source Evidence
→ Confirmed Reference Graph
→ Reverse Sync Candidate
→ Test / Verify
```

## 1. XLSX Intake

Authority:

- `sdlc/config/requirement-intake.yaml`
- `sdlc/scripts/intake_requirements_xlsx.py`

규칙:

1. 고정 Column 번호를 Core 계약으로 요구하지 않는다.
2. Header alias를 탐색하여 Requirement ID/Name/Text를 찾는다.
3. Project별 Header alias는 Overlay/Config로 확장한다.
4. Workbook Row/Hash/Worksheet를 Provenance로 보존한다.
5. Intake는 Canonical ID를 생성하지 않는다.
6. 누락값을 AI가 보완하지 않는다.

## 2. Representative Stage Pack

P2 대표 Pack은 `REQ_TM_TE100`을 `SOURCE_REQUIREMENT`로 유지한다.

- `boundary_status: OPEN`
- Canonical RQ/FR/BR/AC ID: 없음
- Workbook Evidence: `Sheet1!D141:F141`
- Profile: `LITE`
- Brownfield DISCOVERY Required Capability:
  - `source.snapshot.read`
  - `source.search`
- Optional Capability:
  - `source.object.read`

현재 Source Provider가 `UNCONFIGURED`이므로 Required Source Capability만 Block된다.

이 상태에서 다음을 생성하면 실패다.

- 실제 확인되지 않은 Java Class/Method
- 실제 확인되지 않은 API Endpoint
- 실제 확인되지 않은 DB Table/Procedure
- Yellow Page protocol/schema
- Canonical RQ/FR/BR

## 3. Java/Spring Analyzer

Runtime:

- `sdlc/scripts/analyze_java_spring.py`

Adapter는 명시적으로 전달된 파일만 분석한다.

현재 관찰 대상:

- class/interface/enum/record symbol
- Spring route annotation
- transaction annotation
- dependency injection signal

출력은 `OBSERVED`이며 Business Truth를 Confirm하지 않는다.

## 4. SQL/Database Analyzer

Runtime:

- `sdlc/scripts/analyze_sql_database.py`

명시적으로 전달된 SQL File만 분석한다.

현재 관찰 대상:

- TABLE / VIEW
- PROCEDURE / FUNCTION / TRIGGER
- SEQUENCE / INDEX
- FROM/JOIN/UPDATE/INTO/MERGE target
- Dynamic SQL 가능성

Dynamic SQL이 탐지되면 추가 Evidence가 필요하다.

## 5. Interface Analyzer

P2 대표 Requirement가 `Interface` 유형이라고 해서 자동으로 REST/API/File/Message 계약을 결정하지 않는다.

`interface-contract` Analyzer는 현재 `UNCONFIGURED` 상태로 유지한다.

실제 Source Artifact 또는 공식 Interface Specification이 식별된 이후 Adapter를 구성한다.

## 6. Multi-Agent Revision / Ownership Guard

Authority:

- `sdlc/config/version-control-runtime.yaml`
- `sdlc/templates/change-execution-context.yaml`
- `sdlc/scripts/guard_revision_ownership.py`

Source Write 전 필수 조건:

1. `expected_revision == current_revision`
2. Agent Branch 존재
3. Parent Change Branch 존재
4. Write 대상 File이 owned/shared path에 포함
5. Shared File이면 coordination proof 존재
6. 다른 Active Agent Claim과 충돌하지 않음

Guard 결과가 `ALLOW`가 아니거나 `guard_proof_ref`가 없으면 `build_command_context.py`가 `source.write`에 Blocking Human Action을 추가한다.

## 7. Generic E2E /check

Authority:

- `sdlc/config/e2e-orchestration.yaml`
- `sdlc/templates/e2e-execution-ledger.yaml`
- `sdlc/scripts/orchestrate_generic_e2e_status.py`

새 Orchestrator는 근태마감/특정 Requirement Group 이름을 알지 않는다.

Release Ready 조건:

1. 모든 `required_for_release` Stage가 `COMPLETE`
2. `blocks_release=true` Blocker 없음
3. Verification State가 `VERIFIED_PASS`
4. `production_verified=true`

현재 P2 대표 Slice 결과:

- INTAKE: `COMPLETE`
- DISCOVERY: `ACTION_REQUIRED`
- VERIFY: `NOT_STARTED`
- Overall: `ACTION_REQUIRED`
- Release Ready: `false`

## 8. Compatibility

P2는 다음 기존 테스트를 계속 통과해야 한다.

- P1 Foundation
- P1 Runtime
- Structural Redesign v1

기존 `orchestrate_e2e_status.py`는 삭제하지 않고 `COMPATIBILITY_ONLY`로 유지한다.

## 9. P2 완료 기준

P2 구조 검증 완료는 다음을 의미한다.

- 실제 Workbook 직접 Intake 가능
- Source Row Provenance 정확
- 대표 Requirement가 Source ID로 보존됨
- Brownfield Source Provider 미연결 상태를 성공으로 위장하지 않음
- Java/Spring/SQL Adapter가 Domain-independent synthetic fixture에서 동작
- Source Write가 Revision/Ownership Guard 없이 실행되지 않음
- Generic E2E Release Gate가 Domain-independent하게 동작
- P1/Structural Regression PASS

다음 단계에서 실제 고객 Repository/Snapshot을 연결해야 Source Discovery 이후의 Real Vertical Slice를 진행할 수 있다.
