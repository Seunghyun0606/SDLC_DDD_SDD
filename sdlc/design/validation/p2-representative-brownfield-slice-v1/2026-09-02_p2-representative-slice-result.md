# P2 Representative Brownfield Slice — Validation Result

- Date: 2026-09-02
- Branch: `SDLC_DESIGN_SESSION_SECOND/p2/representative-brownfield-slice-v1`
- Base: `SDLC_DESIGN_SESSION_SECOND/p0-p1/structural-redesign-v1`
- Validated Runtime/Docs Head: `717e0ec4704994fa9393a3bf8b8ef83d3f71635a`
- GitHub Actions Run: `33571020192`
- CI Conclusion: `SUCCESS`
- Production Ready: `false`

## Verdict

`P2_CONTROL_PLANE_READY_REAL_SOURCE_REQUIRED`

P2의 목표였던 실제 고객형 Requirement Workbook Intake → 대표 Brownfield Source Requirement → Stage/Provider Runtime Boundary → Generic E2E Status의 Control-plane Vertical Slice는 통과했다.

단, 실제 고객 Source Repository/Snapshot 및 Source Provider가 연결되지 않았으므로 Source Discovery 이후의 Production Vertical Slice는 아직 수행하지 않았다. 현재 상태를 실제 Source 검증 완료 또는 Production Ready로 표현해서는 안 된다.

## 1. Real Workbook Evidence

입력:

- File: `요구사항목록.xlsx`
- SHA-256: `d7dd76d786e97b66435bf4b9dc03fe04b8d55c580b565f2d45817893349ba39f`
- Worksheet: `Sheet1`
- Header Row: `2`
- Source Requirement Rows: `142`
- Duplicate Source Requirement IDs: `0`
- Required Field Missing/Skipped Rows: `0`

대표 Slice:

- Source Requirement ID: `REQ_TM_TE100`
- Actual Workbook Row: `141`
- Evidence Range: `Sheet1!D141:F141`
- Level1: `근태관리`
- Level2: `Interface`
- Requirement Name: `10분단위 근무계획 개선 Yellow Page 송신 반영을 구현`
- Requirement Text: `구성원 근무계획 Yellow Page 송신`
- Truth State: `GIVEN`

검증 중 XLSX Adapter의 Source Row 계산에서 off-by-one 오류를 발견했으며 수정 후 실제 Workbook과 다시 대조하여 Row 141로 고정했다. Regression Test에도 Row 141을 명시적으로 포함했다.

## 2. XLSX Requirement Intake

PASS:

- OOXML 직접 읽기
- 두 행 형태 Header에서 실제 Header Row 자동 식별
- Header Alias 기반 Column Mapping
- 고정 Column 위치 비의존
- Worksheet/File Hash/Actual Source Row Provenance 보존
- Duplicate ID 검사
- Required Field 누락 보존
- Workbook Source Row를 `GIVEN`으로 보존
- Canonical RQ/FR 자동 생성 금지
- Missing Cell 자동 보완 금지

Runtime:

- `sdlc/config/requirement-intake.yaml`
- `sdlc/scripts/intake_requirements_xlsx.py`

## 3. Representative Brownfield Stage Runtime

대표 Stage Pack:

- Target: `REQ_TM_TE100`
- Target Type: `SOURCE_REQUIREMENT`
- Boundary: `OPEN`
- Profile: `LITE`
- Stage: `DISCOVERY`

Brownfield DISCOVERY에서 Runtime Resolver가 결정한 Required Capability:

- `source.snapshot.read`
- `source.search`

Optional Capability:

- `source.object.read`

현재 `provider-registry.example.yaml`의 SOURCE Provider는 `UNCONFIGURED`이므로:

- Required Source Capability → blocking OPEN
- Optional `source.object.read` → non-blocking OPEN
- Command Result → `ACTION_REQUIRED`
- 실제 외부 Source Invocation → `0`

이 동작은 PASS다. 실제 Source가 없는데 Source Evidence/Program/API/DB를 임의 생성하지 않았다.

## 4. Java/Spring Analyzer Adapter

Runtime:

- `sdlc/scripts/analyze_java_spring.py`

Generic synthetic fixture에서 PASS:

- Java class/method 관찰
- Spring route annotation 관찰
- Transaction annotation 관찰
- Dependency injection signal 관찰
- 명시된 File만 분석
- 결과 Truth State `OBSERVED`
- `business_truth_confirmed: false`

실제 고객 Source에는 아직 실행하지 않았다.

## 5. SQL/Database Analyzer Adapter

Runtime:

- `sdlc/scripts/analyze_sql_database.py`

Generic synthetic fixture에서 PASS:

- TABLE 관찰
- PROCEDURE 관찰
- Data Reference 관찰
- Dynamic SQL 가능성 Signal 지원
- 명시된 File만 분석
- 결과 Truth State `OBSERVED`
- `business_truth_confirmed: false`

실제 고객 Source에는 아직 실행하지 않았다.

## 6. Interface Analyzer Boundary

대표 Requirement의 Level2가 `Interface`라는 사실만으로 Yellow Page의 구현 계약을 추측하지 않았다.

현재:

- `interface-contract` Analyzer: `UNCONFIGURED`
- REST/API/File/Message protocol: `UNKNOWN`
- 실제 Interface schema: `UNKNOWN`
- 실제 Source Artifact: `UNKNOWN`

이 상태는 Blocker로 보존한다.

## 7. Revision / Ownership Guard

Authority:

- `sdlc/config/version-control-runtime.yaml`
- `sdlc/templates/change-execution-context.yaml`
- `sdlc/scripts/guard_revision_ownership.py`

PASS:

- Revision match → 계속 평가
- Revision mismatch → `DENY`
- Agent Branch 누락 → `DENY`
- Parent Change Branch 누락 → `DENY`
- Unowned Path → `DENY`
- Shared Path + Coordination Proof 누락 → `DENY`
- Other Agent Active Claim overlap → `DENY`
- 정상 조건 → `ALLOW` + `guard_proof_ref`

`build_command_context.py`와 연결되어 `source.write`는 기존 Write Proof 외에도 Revision/Ownership Guard `ALLOW` + `guard_proof_ref`가 없으면 Blocking Human Action을 생성한다.

## 8. Generic E2E Status

Authority:

- `sdlc/config/e2e-orchestration.yaml`
- `sdlc/templates/e2e-execution-ledger.yaml`
- `sdlc/scripts/orchestrate_generic_e2e_status.py`

기존 근태마감 Group에 종속된 E2E Orchestrator는 `COMPATIBILITY_ONLY`로 이동했다.

대표 Slice 결과:

- INTAKE: `COMPLETE`
- DISCOVERY: `ACTION_REQUIRED`
- VERIFY: `NOT_STARTED`
- Overall: `ACTION_REQUIRED`
- Release Ready: `false`
- Production Verified: `false`

Release Ready Positive Test도 Generic Fixture에서 별도로 PASS했다:

- 모든 Required Stage `COMPLETE`
- Release Blocker 없음
- `VERIFIED_PASS`
- `production_verified: true`
→ `READY_FOR_RELEASE`

## 9. Low-level Agent Contract

신규 Skill:

- `skills/requirement-intake/SKILL.md`
- `skills/revision-ownership-guard/SKILL.md`

각 Skill은 다음을 명시한다.

- Purpose
- Required Input
- Optional Input
- Precondition
- Retrieval Strategy
- Atomic Steps
- Decision Rules
- Output Schema
- Quality Check
- Alert Conditions
- Stop Conditions
- Escalation Conditions
- Do Not
- Normal/Open/Conflict Example

## 10. Regression / CI

Workflow:

`.github/workflows/p2-representative-slice-selftest.yml`

Validated Run `33571020192`:

- Compile P2 Runtime: SUCCESS
- P1 Foundation Compatibility: SUCCESS
- P1 Runtime Compatibility: SUCCESS
- Structural Redesign Regression: SUCCESS
- P2 Representative Slice Tests: SUCCESS

P2 test count: 7

검증 항목:

1. 실제 Workbook Intake Evidence / Row 141
2. Generic two-row XLSX Header Detection / Row Provenance
3. Java/Spring + SQL Analyzer Observation-only
4. Revision/Ownership Guard ALLOW/DENY
5. Brownfield Stage/Provider Runtime가 Real Source Boundary에서 안전하게 정지
6. Source Write Revision Guard Proof 필수
7. Generic E2E Release Gate

## 11. What P2 Proves

YES:

- 실제 XLSX Requirement를 Core Runtime에 직접 Intake 가능
- Project별 Column 위치에 고정되지 않음
- Source Requirement Provenance를 정확히 보존
- 실제 Source Provider 미연결을 성공으로 위장하지 않음
- LITE + Stage Routing + Provider Runtime 연결 유지
- Java/Spring/SQL Analyzer를 Core와 분리된 Adapter로 추가 가능
- Multi-Agent Source Write용 Revision/Ownership Guard 존재
- E2E Status가 특정 근태 Domain 없이 동작
- P1/Structural Redesign Regression 유지

## 12. What P2 Does Not Prove

NO / NOT RUN:

- 실제 고객 Repository/Snapshot Source Discovery
- 실제 Yellow Page Interface 계약 분석
- 실제 Java/Spring Source의 Trace
- 실제 SQL/Procedure/Trigger Trace
- Batch/Scheduler Adapter
- Interface-contract Adapter
- 실제 Source Write Provider
- 실제 Canonical Registry
- 실제 Runtime Test Provider
- 실제 Source → Reverse Sync → Verification E2E
- Production Verification
- Production Ready

## 13. Remaining Blocking Inputs

### External / Customer Inputs

1. 실제 Source Repository 또는 Snapshot
2. Source Revision
3. Source Provider 접근 방법/권한
4. 실제 Test Command/Runtime Environment
5. Interface Specification이 별도로 존재한다면 해당 공식 Source

### Harness P3/P2.1 Implementation

1. Interface-contract Analyzer Adapter
2. Batch/Scheduler Analyzer Adapter
3. 실제 Source Provider Adapter 검증
4. Worklist MD ↔ XLSX Runtime Sync
5. Requirement Intake → Worklist 자동 등록
6. Representative Slice의 실제 Source Discovery → Reference Graph → Reverse Sync → Verify

## Final State

```text
P0 Safety Contract                   PRESERVED
P1 Foundation                        PASS_REGRESSION
Structural Redesign                  PASS_REGRESSION
Real XLSX Requirement Intake         PASS
Source Row Provenance                PASS
Representative Control-plane Slice   PASS
Java/Spring Adapter Contract         PASS_SYNTHETIC
SQL/Database Adapter Contract        PASS_SYNTHETIC
Interface Adapter                    UNCONFIGURED
Revision/Ownership Guard             PASS_SYNTHETIC
Generic E2E Status                   PASS
Real Customer Source Slice           BLOCKED_EXTERNAL_INPUT
Production Verification              NOT_RUN
Production Ready                     false
```

## Recommendation

다음 단계는 Core 문서를 더 확장하는 것이 아니라 실제 고객 Source Repository/Snapshot을 연결한 뒤 `REQ_TM_TE100` 또는 Source Artifact가 확인 가능한 다른 대표 Requirement 1건에 대해 다음을 실행하는 것이다.

`Requirement Intake → Bounded Source Discovery → Adapter Analysis → Confirmed/OPEN Reference Graph → Impact → Design → guarded Source Change → Runtime Test → Reverse Sync → Verification`

실제 Source가 제공되지 않는 동안에는 Interface/Program/Table 구조를 추측하여 다음 단계가 완료된 것처럼 만들지 않는다.
