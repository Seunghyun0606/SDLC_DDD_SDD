# P0 Runtime Core Redesign v1 — Validation Result

> Branch: `SDLC_DESIGN_SESSION_SECOND/p0.redesign/runtime-core-v1`
> Base: `SDLC_DESIGN_SESSION_SECOND/p0.final/design-baseline-exit-v1`
> Date: 2026-09-02
> Main merge: **NOT PERFORMED**

## Verdict

**P0 RUNTIME CORE REDESIGN: IMPLEMENTED / RUNTIME TEST NOT YET EXECUTED**

Machine state:

`P0_RUNTIME_CORE_IMPLEMENTED_TEST_EVIDENCE_OPEN`

Production Ready: `false`

Real Brownfield Vertical Slice Ready: `PARTIAL`

이 결과는 P0의 구조 재설계 구현을 의미한다. 새 Runtime conformance test는 Repository에 작성했으나 현재 세션 환경에서는 Branch를 별도 Local Checkout하여 Python Runtime으로 실행한 증거를 만들지 못했으므로 PASS를 주장하지 않는다.

## 1. Redesign Scope

이번 P0 재설계는 다음 문제를 우선 해결한다.

1. `/work`가 호출자에게 Capability 목록을 미리 요구하던 구조
2. Stage/Skill/Next Stage가 문서와 Runtime 여러 곳에 분산된 구조
3. Stage Input Pack에서 ART/SYMBOL/DATA/INT/SOURCE Trace가 유실되는 구조
4. Java/MyBatis/Attendance Fixture가 범용 Source Discovery/Reverse Sync Core처럼 존재하던 구조
5. `/setup`이 문서에는 Command이나 Runtime Router에는 없던 불일치
6. Low-Agent Skill Contract가 실제 활성 Skill에 강제되지 않던 문제
7. `/check`가 Full SDLC가 아니라 P0 Fixture Stage에 과도하게 결합된 문제
8. `/change` Reverse Sync의 Semantic 판단이 Stack/Pilot Heuristic에 결합된 문제

## 2. Implemented Runtime Core

### 2.1 Single Stage Routing Authority

Authority:

`sdlc/config/stage-routing.yaml`

Full Stage Order:

```text
INTAKE
→ DECOMPOSE
→ CLARIFY
→ PROCESS
→ DISCOVERY
→ IMPACT
→ DESIGN
→ PROGRAM
→ DEVELOPMENT
→ TEST
→ VERIFY
→ KNOWLEDGE
```

`/work`는 `project_context.stage`를 기준으로 다음을 결정한다.

- Skill
- Procedure Profile
- Agent Level
- Required Input Types
- Provider Capability Candidates
- Expected Outputs
- Next Stage

### 2.2 Consolidated Stage Procedure

반복되는 문서형 Stage마다 별도 `SKILL.md`를 추가하지 않는다.

공통 Skill:

`sdlc/starter/onboarding-package-v1/skills/stage-procedure/SKILL.md`

Procedure Authority:

`sdlc/config/stage-procedures.yaml`

공통 Procedure Profile:

- DECOMPOSE
- CLARIFY
- PROCESS
- IMPACT
- DESIGN
- PROGRAM
- KNOWLEDGE
- CHANGE_CONTROL
- STATUS_READ_MODEL
- PROJECT_SETUP

### 2.3 Typed Stage Input Pack v2

Trace Identity:

`RQ / FR / BR / PROC / FTR / PGM / ART / SYMBOL / DATA / INT / AC / TC / TASK / CR / KNOWLEDGE / SOURCE`

Typed Handoff:

- Required Input
- Resolved Fact
- Evidence
- OPEN Item
- Expected Output
- Current/Next Skill
- Current/Next Procedure Profile
- Agent Level
- Next Action

Builder:

`sdlc/scripts/build_stage_handoff.py`

Agent가 Next Stage/Skill/Output Contract를 임의 추론하는 것을 줄인다.

## 3. Generic Source / Analyzer Boundary

Core Runtime은 Stack-specific Source Syntax를 직접 해석하지 않는다.

Boundary:

`sdlc/adapters/analyzers/README.md`

Analyzer Capability Candidate:

```text
analysis.source.symbols
analysis.source.dependencies
analysis.source.data_refs
analysis.source.interface_refs
```

활성 Discovery Skill:

`sdlc/starter/onboarding-package-v1/skills/source-discovery/SKILL.md`

기존 아래 Script의 Java/MyBatis/Attendance Fixture 로직은 Core Authority에서 제외했다.

- `sdlc/scripts/discover_source_evidence.py`
- `sdlc/scripts/build_reverse_sync_candidate.py`

파일은 P0 호환/Validation Reference로 남아 있으나 신규 Runtime Core의 범용 Source Analyzer로 취급하지 않는다.

## 4. Requirement Intake Generalization

활성 INTAKE는 Legacy Excel Grouping Skill을 직접 사용하지 않는다.

Active:

`sdlc/starter/onboarding-package-v1/skills/requirement-intake/SKILL.md`

Legacy Reference:

`sdlc/starter/onboarding-package-v1/skills/sop-business-extraction/SKILL.md`

Core Intake는 특정 Column/Domain/Pilot Grouping Rule 없이 Source ID/Locator/Requirement Intent를 보존한다.

## 5. Provider Runtime Changes

Provider Router는 Required와 Optional Capability를 구분한다.

- Required Capability missing → Action Block
- Optional Read/Evidence Capability missing → OPEN/PARTIAL

`/setup` Runtime Capability를 추가했다.

Source Analyzer Provider Type을 추가했다.

Side-effect Capability는 Stage가 허용하고 실행 Context가 명시적으로 요청한 경우만 Required/Write Capability가 된다.

현재 TEST의 명시적 Side Effect:

`test.execute`

## 6. Development / Source Write

Development Skill은 Greenfield/Brownfield/Hybrid 공통으로 일반화했다.

기본 Write Mode:

`PROPOSAL_ONLY`

현재 P0 Runtime Core v1에서는 Source Write Capability를 아직 표준화하지 않았다.

따라서 실제 Source 변경은 이 Exit Criteria에 포함하지 않는다.

다음 P0 작업에서 `source.patch.apply` 또는 동등한 Capability Contract를 정의하기 전에는 Source Change Proposal까지만 범용 Core 보장 범위다.

## 7. Controlled Generic Reverse Sync

Generic Builder:

`sdlc/scripts/build_reverse_sync_generic.py`

Source Diff Template:

`sdlc/templates/source-diff-evidence.yaml`

Reference Graph:

`sdlc/templates/reference-graph.yaml`

Core Reverse Sync 규칙:

```text
Changed Path/Symbol/Data/Interface Ref
→ Direct Trace Node
→ CONFIRMED Graph Edge만 역방향 탐색
→ PGM/ART/SYMBOL/DATA/INT = STALE_CANDIDATE
→ RQ/FR/BR/PROC/FTR/AC/TC = REVIEW_CANDIDATE
→ Human Truth Protected
```

Semantic Change Class는 Core가 Java/MyBatis/Domain Constant를 보고 추론하지 않는다.

Analyzer/Provider/Human Evidence가 만든 Class를 소비한다.

Non-confirmed Trace Edge는 조용히 따라가지 않고 Review 대상으로 남긴다.

## 8. Full Stage `/check` Read Model

Generic Builder:

`sdlc/scripts/build_status_view.py`

기존 P0 Fixture 중심 E2E Status Script 대신 12개 전체 Stage Input Pack을 읽어 다음 상태를 계산할 수 있도록 분리했다.

- NOT_STARTED
- PARTIAL
- ACTION_REQUIRED
- COMPLETE_WITH_OPEN
- COMPLETE

Read Model은 Business Truth를 생성하지 않는다.

## 9. Low-Agent Guard

새 Validator:

`sdlc/scripts/validate_routed_skills.py`

전체 Legacy Skill을 한 번에 강제하지 않고 **현재 Stage Routing에서 실제 도달 가능한 Skill만** Low-Agent 14 Section Contract로 검사한다.

활성 Routed Skill 수는 Stage별 별도 Skill 난립 대신 다음 핵심 Skill 중심으로 축소했다.

- requirement-intake
- stage-procedure
- source-discovery
- source-change
- test-verification

필수 Section:

`Purpose → Required Input → Optional Input → Precondition → Retrieval Strategy → Atomic Steps → Decision Rules → Output Schema → Quality Check → Alert Conditions → Stop Conditions → Escalation Conditions → Do Not → Example`

## 10. Deterministic Validation Assets

추가/갱신한 P0 검증 구성:

- `sdlc/scripts/validate_p0_runtime_core.py`
- `sdlc/scripts/validate_routed_skills.py`
- `sdlc/design/validation/p0-runtime-core-redesign-v1/test_runtime_core.py`

Conformance Test Definition은 다음을 검증하도록 작성했다.

1. Stage Routing / Procedure Profile 정합성
2. Routed Skill 파일 및 Low-Agent Section Contract
3. Stage Input Pack v2 Handoff 자동 생성
4. Brownfield Source/Analyzer Provider 미설정 시 PARTIAL/OPEN 유지
5. Greenfield 문서형 Stage 진행
6. `/change`의 optional `source.diff`와 Generic Reverse Sync
7. `/check`의 Full 12 Stage Read Model
8. Explicit `test.execute` Side-effect Blocking
9. `/setup` Runtime Route
10. Unknown Stage 추측 금지

### Runtime Evidence State

`NOT_RUN_IN_THIS_SESSION`

현재 세션에서는 GitHub Branch를 Local Checkout하여 Python suite를 실행할 수 있는 네트워크 Runtime Evidence가 확보되지 않았다.

따라서 다음을 주장하지 않는다.

- `test_runtime_core.py PASS`
- 기존 P0/P1 전체 Regression PASS
- 실제 고객 Project PASS
- Production Ready

## 11. Change Size

Base 대비 GitHub Compare 기준:

- Ahead commits: 38
- Behind commits: 0
- Changed files: 23

주요 변경 영역:

- `sdlc/config`
- `sdlc/templates`
- `sdlc/scripts`
- `sdlc/starter/onboarding-package-v1/skills`
- `sdlc/adapters/analyzers`
- `sdlc/design/contracts`
- `sdlc/design/validation`

`main`에는 Merge하지 않았다.

## 12. Confirmed Improvements

구조적으로 다음 문제는 P0 Runtime Core v1에서 직접 수정됐다.

- `/work` Capability 사전 주입 의존 축소
- Full Stage Order 단일 Authority
- `/setup` 문서/Runtime Command 불일치 제거
- Typed Handoff Trace 확장
- Stage별 SKILL 파일 증가 억제
- 활성 INTAKE의 Pilot Grouping 의존 제거
- Core와 Stack-specific Analyzer 경계 명시
- Missing Read Provider와 Blocking Action 분리
- Stack-neutral Reverse Sync Builder 추가
- Full SDLC Status Read Model 추가
- 활성 Routed Skill Low-Agent 검증 추가

## 13. Remaining P0 Blockers

### P0-R1 — Actual Runtime Conformance Execution

Repository Checkout 환경에서 다음을 실제 실행해야 한다.

```text
python sdlc/scripts/validate_p0_runtime_core.py bundle sdlc/config/stage-routing.yaml --procedures sdlc/config/stage-procedures.yaml
python sdlc/scripts/validate_p0_runtime_core.py stage-pack sdlc/templates/stage-input-pack.yaml
python sdlc/scripts/validate_routed_skills.py sdlc/config/stage-routing.yaml sdlc/starter/onboarding-package-v1/skills
python sdlc/design/validation/p0-runtime-core-redesign-v1/test_runtime_core.py
```

### P0-R2 — Regression Compatibility

기존 P0.x/P1 Validator/Test와 새 Generic Template의 호환성을 확인해야 한다.

특히 `source-diff-evidence.yaml` v2 변경과 Legacy Fixture Validator 간 계약을 점검한다.

### P0-R3 — Source Write Capability

실제 Source 변경을 범용 Core에서 지원하려면 다음을 별도 계약으로 추가해야 한다.

- Source Write Capability
- Expected Revision
- Patch/Change Payload
- Permission Proof
- Idempotency
- UNKNOWN_AFTER_WRITE Recovery
- Post-write Diff Evidence

그 전까지 Development Default는 `PROPOSAL_ONLY`다.

### P0-R4 — Human Artifact Runtime Mapping

Artifact Profile이 요구하는 고객/프로젝트용 Human Artifact를 실제 Template Path와 연결하는 Mapping을 추가해야 한다.

중복 Template을 만들지 않고 기존 Customer Functional Spec / Development Blueprint를 재사용하는 방향이 우선이다.

### P0-R5 — Real Vertical Slice

P0 Runtime Core가 안정화된 후 실제 Customer Source 기반 Representative Requirement 1건으로 다음을 검증해야 한다.

```text
INTAKE
→ DECOMPOSE
→ PROCESS/DISCOVERY
→ IMPACT
→ DESIGN
→ PROGRAM
→ DEVELOPMENT Proposal/Write
→ TEST
→ VERIFY
→ /change Reverse Sync
→ /check Resume
```

## Final State

```text
Stage Routing Authority = IMPLEMENTED
Shared Stage Procedure = IMPLEMENTED
Typed Handoff v2 = IMPLEMENTED
Generic Requirement Intake = IMPLEMENTED
Generic Source Analyzer Boundary = IMPLEMENTED
Optional Read Provider Semantics = IMPLEMENTED
Generic Reverse Sync Candidate = IMPLEMENTED
Full Stage Status Read Model = IMPLEMENTED
Low-Agent Routed Skill Validation = IMPLEMENTED
Actual Source Write Capability = NOT YET STANDARDIZED
Runtime Conformance Execution = NOT RUN
Regression Suite = NOT RUN
Real Customer Vertical Slice = NOT RUN
Production Ready = false
```

## Next Recommended P0 Work

1. Runtime/Regression suite 실제 실행 가능 환경에서 conformance 확인
2. Legacy P0.x Compatibility 문제 수정
3. Source Write Capability + Recovery 연결
4. Artifact Profile → Human Template Mapping 단순화
5. 실제 Generic Greenfield/Brownfield Fixture 각각 1건 통과
6. 그 후 P0 Redesign Exit Review
