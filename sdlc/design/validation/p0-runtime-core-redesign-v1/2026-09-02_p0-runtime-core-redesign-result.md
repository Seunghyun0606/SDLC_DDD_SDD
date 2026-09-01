# P0 Runtime Core Redesign v1 — Exit Validation Result

> Branch: `SDLC_DESIGN_SESSION_SECOND/p0.redesign/runtime-core-v1`
> Base: `SDLC_DESIGN_SESSION_SECOND/p0.final/design-baseline-exit-v1`
> Date: 2026-09-02
> Main merge: **NOT PERFORMED**

## Verdict

**P0 RUNTIME CORE REDESIGN EXIT: PASS**

Machine state:

`P0_RUNTIME_CORE_READY`

Production Ready: `false`

P1 Entry: `ALLOWED`

P0 Runtime Core 범위의 미해결 Blocker: **NONE**

실제 고객 Repository Vertical Slice, Production Source Write Adapter, 실제 CI Test Adapter는 P0 Runtime Core의 범용 계약 완성 조건이 아니라 P1/Project Binding 검증 항목으로 분리한다.

---

## 1. Exit Evidence

최종 READY commit:

`162fbe65b13458d06c88d3c16638453b9338c155`

GitHub Actions:

- Workflow: `.github/workflows/p0-runtime-core.yml`
- Run ID: `33545534076`
- Conclusion: `success`

동일 Run에서 다음이 모두 성공했다.

1. `Validate P0 runtime exit gate` — SUCCESS
2. `Run redesigned P0 runtime conformance` — SUCCESS
3. `Run legacy P0 regression suite` — SUCCESS

직전 Regression 상세 Run에서도 다음 11개 Legacy P0 Test가 전부 PASS했다.

- `test_p01_contracts.py`
- `test_p02_contracts.py`
- `test_p03_contracts.py`
- `test_p04_contracts.py`
- `test_p05_orchestration.py`
- `test_p06_contracts.py`
- `test_p07_conformance.py`
- `test_p08_runtime.py`
- `test_p09_command_runtime.py`
- `test_p0_contracts.py`
- `test_p0_exit.py`

따라서 이번 Exit는 문서상 선언이 아니라 실제 Branch CI 실행 결과를 근거로 한다.

---

## 2. P0 Runtime Core Authority

### 2.1 Stage Routing

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

`/work`는 더 이상 호출자가 Capability 목록을 사전에 계산해야 하는 단순 Dispatcher가 아니다.

현재 Stage와 Project Mode를 기준으로 다음을 결정한다.

- Skill
- Procedure Profile
- Agent Level
- Required Input Type
- Optional/Required Provider Capability
- Explicit Side-effect 허용 범위
- Expected Output
- Next Stage

`/change`, `/check`, `/setup`도 동일 Routing Authority에 포함한다.

### 2.2 Shared Stage Procedure

반복되는 문서형 Stage마다 별도 Skill을 만들지 않는다.

- Shared Skill: `sdlc/starter/onboarding-package-v1/skills/stage-procedure/SKILL.md`
- Procedure Authority: `sdlc/config/stage-procedures.yaml`

Procedure Profile:

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

도구/위험 계약이 특별한 단계만 독립 Skill을 유지한다.

---

## 3. Typed Stage Handoff v2

Authority:

`sdlc/templates/stage-input-pack.yaml`

Builder:

`sdlc/scripts/build_stage_handoff.py`

Typed Trace:

`RQ / FR / BR / PROC / FTR / PGM / ART / SYMBOL / DATA / INT / AC / TC / TASK / CR / KNOWLEDGE / SOURCE`

Handoff에는 다음을 구조화한다.

- Required Input
- Resolved Fact
- Evidence
- OPEN Item
- Constraints
- Expected Output
- Current/Next Skill
- Current/Next Procedure Profile
- Agent Level
- Next Action

다음 Agent가 Conversation History 없이도 Stage Route와 Output Contract를 다시 추론하는 부담을 줄였다.

---

## 4. Generic Greenfield / Brownfield Validation

Fixture:

`sdlc/design/validation/p0-runtime-core-redesign-v1/fixtures/`

포함 Scenario:

- Generic Greenfield Requirement Intake
- Generic Brownfield Discovery
- Generic Brownfield Source Diff
- Generic Brownfield Reference Graph

### Greenfield

Source Provider가 없어도 INTAKE가 정상 시작되고 `DECOMPOSE`로 Handoff 가능함을 검증했다.

### Brownfield

Source/Analyzer Provider가 미설정이면 전체 Workflow를 BLOCK하지 않고 필요한 Evidence를 `OPEN/PARTIAL`로 보존함을 검증했다.

Fixture는 Attendance/Java/MyBatis/TB_* 용어를 사용하지 않는다.

---

## 5. Source / Analyzer Boundary

활성 Core는 Stack-specific Source Syntax를 직접 해석하지 않는다.

Analyzer Boundary:

`sdlc/adapters/analyzers/README.md`

Capability:

```text
analysis.source.symbols
analysis.source.dependencies
analysis.source.data_refs
analysis.source.interface_refs
```

기존 아래 Script는 Legacy Fixture/Validation Reference로 남지만 Core Authority가 아니다.

- `sdlc/scripts/discover_source_evidence.py`
- `sdlc/scripts/build_reverse_sync_candidate.py`

즉 Java/MyBatis/근태 Sample Parser가 범용 Brownfield Core를 정의하지 않는다.

---

## 6. Controlled Source Write

Capability:

`source.patch.apply`

Contract:

`sdlc/design/contracts/source-write-capability.md`

Provider Registry에는 Reference Source Writer Entry가 존재하지만 기본값은:

```text
enabled = false
provider_state = DISABLED
mode = READ_WRITE
default execution = PROPOSAL_ONLY
```

실제 Write는 다음이 모두 필요하다.

- 현재 Stage가 해당 Side-effect를 허용
- `requested_side_effect_capabilities`에 명시
- Expected Revision
- Permission Proof
- Idempotency Key
- 사용할 수 있는 READ_WRITE Source Provider

기존 `write_capabilities` 필드만 직접 주입해 Write Guard를 우회하는 경로는 차단했다.

Write 응답이 유실되면 자동 성공/재시도하지 않고 `UNKNOWN_AFTER_WRITE → RECOVERY_REQUIRED`를 유지한다.

Production Source Writer 구현은 Project Adapter/P1 범위다.

---

## 7. Test Side-effect Guard

`test.execute`도 Source Write와 같은 Explicit Side-effect 규칙을 적용한다.

Proof 없이 실행을 요청하면 Provider 호출 전에 Plan 단계에서 `INVALID`다.

Proof가 존재하더라도 Test Provider가 unavailable이면 해당 실행 Action만 `ACTION_REQUIRED`가 되며, Test 설계/비실행 상태는 별도로 보존한다.

`Runtime PASS requires execution evidence` invariant는 유지한다.

---

## 8. Generic Reverse Sync

Builder:

`sdlc/scripts/build_reverse_sync_generic.py`

Core Flow:

```text
Source Diff
→ Changed Path/Symbol/Data/Interface Ref
→ Direct Trace Node
→ CONFIRMED Graph Edge Traversal
→ Technical Node STALE_CANDIDATE
→ Business Truth REVIEW_CANDIDATE
→ Human Truth Protected
```

Generic Brownfield Fixture에서:

- Changed `ART` → `STALE_CANDIDATE`
- 관련 `FR/RQ` → `REVIEW_CANDIDATE`
- Human Truth 자동 overwrite 금지

을 검증했다.

Core는 Domain Constant/Java 문법/MyBatis Mapper 이름으로 Business Rule을 자동 확정하지 않는다.

---

## 9. Full `/check` Read Model

Builder:

`sdlc/scripts/build_status_view.py`

12개 전체 Stage를 읽어 다음을 계산한다.

- NOT_STARTED
- PARTIAL
- ACTION_REQUIRED
- COMPLETE_WITH_OPEN
- COMPLETE

Read Model은 Business Truth나 PASS를 새로 만들지 않는다.

---

## 10. Low-Agent Execution Guard

Validator:

`sdlc/scripts/validate_routed_skills.py`

활성 Runtime Route에서 실제 도달 가능한 Skill만 Low-Agent 14 Section Contract로 강제한다.

핵심 Routed Skill:

- requirement-intake
- stage-procedure
- source-discovery
- source-change
- test-verification

필수 구조:

`Purpose → Required Input → Optional Input → Precondition → Retrieval Strategy → Atomic Steps → Decision Rules → Output Schema → Quality Check → Alert Conditions → Stop Conditions → Escalation Conditions → Do Not → Example`

Legacy/Reference Skill 전체를 한꺼번에 Runtime 필수 계약으로 만드는 과설계는 피했다.

---

## 11. Human Artifact Simplification

Artifact Profile은 Logical Artifact Role 수와 Physical Document 수를 동일하게 강제하지 않는다.

기본 Human-facing Physical View는 다음 중심으로 수렴한다.

1. 전체작업목록
2. 고객 기능정의서
3. Engineering Blueprint
4. 구현·검증 결과서

Mapping:

- 요구/프로세스/6W → 고객 기능정의서
- 영향/기능설계/프로그램설계 → Engineering Blueprint
- 구현/Test/Verify → 구현·검증 결과서

내부 Canonical Trace와 Guard는 문서 수 축소와 무관하게 유지한다.

---

## 12. Machine-readable Exit Gate

Authority:

`sdlc/config/p0-runtime-core-exit.yaml`

Validator:

```text
python sdlc/scripts/validate_p0_runtime_core.py exit sdlc/config/p0-runtime-core-exit.yaml
```

Exit Gate가 검사하는 주요 항목:

- Required Authority/Runtime/Fixture/Test 존재
- Routed Skill 존재
- Branch CI Workflow 존재
- Stage/Write Safety Invariant
- Source Writer 기본 DISABLED
- Active Core의 Pilot Token 유출 금지
- Production/P1 항목이 P0 완료조건으로 잘못 포함되지 않았는지 확인

CI에서 실제 PASS했다.

---

## 13. Regression Finding and Fix

첫 CI 실행에서 새 Runtime Conformance는 PASS했으나 Legacy P0.9 Command Runtime Regression이 실패했다.

원인:

기존 P0.9 Test가 Stage Router 이전 모델을 전제로 `/work`에 임의 Capability와 Write Capability를 직접 주입했다.

검토 중 더 중요한 안전 문제를 확인했다.

Legacy `write_capabilities` 직접 주입이 Stage Side-effect Allow-list를 우회할 가능성이 있었다.

수정:

- 모든 Write는 `requested_side_effect_capabilities`에 명시되어야 함
- 현재 Stage Side-effect Allow-list에 존재해야 함
- Proof Preflight를 Provider Plan 이전에 수행
- Legacy 직접 Write 주입은 `INVALID`
- UNKNOWN_AFTER_WRITE Test는 정식 `source.patch.apply` 경로로 변경

수정 후 새 Conformance와 Legacy Regression이 모두 PASS했다.

---

## 14. P0 Exit vs Production Readiness

P0 Runtime Core Exit가 PASS했다고 다음을 의미하지 않는다.

- 실제 고객 Repository가 검증됨
- 실제 Production Source Writer가 연결됨
- Jenkins/GitHub Actions/Azure DevOps Test Adapter가 연결됨
- Monitoring/Deployment Provider가 구현됨
- 실제 Release가 가능함

이들은 다음 단계의 Project/P1/P2 Evidence다.

P0에서 완료한 것은:

**“특정 Sample/Stack에 종속되지 않는 Runtime Core 계약과 deterministic safety boundary가 존재하고, Generic Greenfield/Brownfield Fixture 및 기존 P0 Regression을 통과한다.”**

이다.

---

## 15. Deferred Non-P0 Items

| 항목 | 단계 | 이유 |
|---|---|---|
| 실제 고객 Brownfield Vertical Slice | P1 | Project binding과 실제 Source Evidence 검증 |
| Production Source Write Adapter | P1 / Project Adapter | Core는 Capability/Safety Contract까지만 책임 |
| 실제 CI Test Adapter | P1 / Project Adapter | Jenkins/GHA/Azure DevOps 구현 차이 |
| Monitoring/Deployment Provider | P2 | P0 Runtime Core Exit 필수 요건 아님 |

---

## Final State

```text
Stage Routing Authority = PASS
Shared Stage Procedure = PASS
Typed Handoff v2 = PASS
Generic Requirement Intake = PASS
Generic Greenfield Fixture = PASS
Generic Brownfield Fixture = PASS
Generic Source Analyzer Boundary = PASS
Optional Read Provider Semantics = PASS
Source Write Capability Contract = PASS
Source Writer Default Disabled = PASS
Write Proof Preflight = PASS
Legacy Write Bypass Guard = PASS
UNKNOWN_AFTER_WRITE Recovery = PASS
Generic Reverse Sync = PASS
Full 12-Stage Status Read Model = PASS
Low-Agent Routed Skill Validation = PASS
Human Artifact Mapping = PASS
P0 Runtime Exit Gate = PASS
Redesigned Runtime Conformance = PASS
Legacy P0 Regression = PASS (11 scripts)
P0 Runtime Core Blocker = NONE
P0 Runtime Core State = P0_RUNTIME_CORE_READY
P1 Entry = ALLOWED
Production Ready = false
Main Merge = NOT PERFORMED
```

## Exit Decision

**P0 Runtime Core 재설계는 종료한다.**

다음 작업은 P0 Core를 다시 확장하는 것이 아니라, 이 `P0_RUNTIME_CORE_READY` 기준 위에서 P1의 실제 Project Foundation / Vertical Slice / Adapter Binding을 검증하는 것이다.
