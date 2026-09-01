# P0 Runtime Core Redesign Contract

상태: `ACTIVE_P0_REDESIGN`

## 1. 목적

기존 P0의 Truth/Safety Guard는 유지하면서 `/work` 실행 경로를 단일화한다.

P0 재설계의 핵심은 다음 네 가지다.

1. Stage 선택은 코드에 흩어진 조건이 아니라 `sdlc/config/stage-routing.yaml`이 결정한다.
2. 다음 Agent는 대화 History 없이 Typed Stage Input Pack만으로 Trace와 OPEN을 이어받을 수 있어야 한다.
3. Java/MyBatis/특정 업무와 같은 Stack/Domain 파싱은 Core Script에서 수행하지 않는다.
4. Provider가 없거나 읽기 결과가 PARTIAL이면 Business Truth를 만들지 않고 OPEN/PARTIAL로 진행한다.

## 2. 유지하는 P0 안전장치

다음은 단순화를 이유로 제거하지 않는다.

- Human Truth와 Source Evidence 분리
- Candidate와 Canonical 분리
- Source Revision/Hash Evidence
- Test Design Coverage와 Runtime PASS 분리
- 실행하지 않은 Test의 PASS 금지
- Write Permission + Idempotency
- `UNKNOWN_AFTER_WRITE` Recovery
- OPEN Preservation
- 위험한 Side-effect Action만 Guard

## 3. 단일 Stage Routing Authority

Authority:

`sdlc/config/stage-routing.yaml`

표준 Stage:

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

`/work` Runtime은 `project_context.stage`를 읽어 다음을 결정한다.

- Skill
- Agent Level
- Required Input Type
- Provider Capability Candidate
- Expected Output Type
- Next Stage

호출자가 `requested_capabilities`를 모두 미리 계산해 주는 방식은 호환성 입력으로만 남긴다.

## 4. Provider Capability 의미

Capability는 두 종류로 구분한다.

### 4.1 Read / Evidence Capability

예:

- `source.search`
- `source.object.read`
- `source.snapshot.read`
- `test.result.read`

Provider가 없으면 기본적으로 `OPEN`이다. 해당 Source/Test claim은 만들 수 없지만 전체 SDLC Workflow를 정지시키지 않는다.

### 4.2 Side-effect Capability

예:

- `test.execute`
- 향후 `source.patch.apply`
- 향후 `deployment.execute`

Stage Config에 허용되어 있고 실행 Context가 명시적으로 요청한 경우만 호출한다.

Side-effect는 기존 Permission/Idempotency/Recovery Contract를 반드시 통과한다.

## 5. Typed Stage Input Pack v2

`related_ids`는 최소 다음 Identity를 보존한다.

`RQ / FR / BR / PROC / FTR / PGM / ART / SYMBOL / DATA / INT / AC / TC / TASK / CR / KNOWLEDGE / SOURCE`

또한 다음 목록은 free-form 문자열 목록이 아니라 Type/Ref/State를 갖는 구조로 전달한다.

- Required Input
- Resolved Fact
- Evidence
- OPEN Item
- Expected Output
- Next Action

핵심 목적은 다음 Agent가 다음을 재추론하지 않게 하는 것이다.

1. 무엇을 입력으로 사용해야 하는가?
2. 어떤 사실이 확정/관찰/추론/미확정인가?
3. 어떤 Source/Data/Test Evidence가 사용되었는가?
4. 무엇을 출력해야 하는가?
5. 어떤 Action이 Side Effect인가?
6. 다음 Stage와 Skill은 무엇인가?

## 6. Stack-specific Analyzer Boundary

Core는 다음을 직접 하드코딩하지 않는다.

- Java Method Regex
- MyBatis XML 규칙
- 특정 Table prefix
- 특정 Procedure 이름 규칙
- 특정 Domain constant
- Sample/Pilot Requirement ID

Stack-specific 분석 구현 위치:

`sdlc/adapters/analyzers/<stack-or-provider>/`

Analyzer는 Provider/Capability 계약으로 다음과 같은 Evidence를 반환할 수 있다.

- Symbol
- Dependency
- Data Reference
- Interface Reference

Core는 Analyzer의 결과를 `OBSERVED` Evidence로 소비할 뿐 Business Truth로 자동 승격하지 않는다.

Analyzer가 없는 Stack은 `UNSUPPORTED_STACK / OPEN`으로 보존하며 L2/L3 Adapter 구현 후보를 만든다.

## 7. `/setup` 정합성

문서에서 관리자 진입점으로 제공하는 `/setup`은 Runtime Router에도 정식 Command Capability로 존재해야 한다.

일반 사용자의 기본 Command는 계속 다음 세 개다.

`/work /change /check`

`/setup`은 Harness 관리자용이다.

## 8. Low-Agent 기준

P0 Runtime Core가 해결하는 것은 Stage 선택과 Handoff의 결정성이다.

P0 완료 후에도 Business Boundary, Architecture Decision, 고위험 Source Change 등은 L2/Human이 필요할 수 있다.

L1을 억지로 모든 Stage에 투입하지 않는다.

다만 L1이 맡는 Stage에서는 다음이 반드시 기계 검증 가능해야 한다.

- Required Input 존재
- Stable ID Reference
- Evidence Reference
- OPEN Preservation
- Output Type
- Next Stage
- Side-effect 여부

## 9. 기존 P0 Artifact 처리

기존 P0.x Artifact를 즉시 삭제하지 않는다.

분류 원칙:

- Safety Contract: 유지
- Compatibility Input/Output: 당분간 유지
- Fixture/Pilot Script: Validation 영역 또는 Analyzer Adapter로 이동
- 중복 Stage Truth: `stage-routing.yaml`을 Authority로 전환
- E2E Read Model: Stage Routing을 읽도록 후속 변경

특히 기존 `discover_source_evidence.py`, `build_reverse_sync_candidate.py`의 Stack/Pilot-specific 구현은 새로운 Runtime Core에서 권위 있는 범용 Analyzer로 간주하지 않는다.

## 10. P0 Redesign Exit Criteria

다음이 충족되면 Runtime Core v1 P0 재설계의 첫 Exit로 본다.

1. `/work`가 Stage Config에서 Skill/Capability/Output/Next Stage를 도출한다.
2. Missing Read Provider가 전체 Workflow를 자동 중지시키지 않는다.
3. Explicit Side-effect Capability만 Write/Test Execution 대상으로 호출된다.
4. `/setup` 문서와 Runtime이 일치한다.
5. Stage Input Pack v2가 전체 Trace Identity를 보존한다.
6. Stage Routing과 Stage Pack에 Deterministic Validator가 존재한다.
7. Stack-specific Source Syntax는 Core Runtime 계약 밖으로 분리된다.
8. P0 Validation Fixture가 위 규칙을 검증한다.

이 Exit는 실제 고객 Brownfield Vertical Slice PASS 또는 Production Ready를 의미하지 않는다.
