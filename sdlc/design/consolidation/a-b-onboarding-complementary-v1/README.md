# A+B+Onboarding Complementary Consolidation v1

> Branch: `SDLC_DESIGN_SESSION_SECOND/consolidation/a-b-onboarding-complementary-v1`
> Status: `CONSOLIDATED VALIDATION / NOT MAIN BASELINE`

## Goal

Candidate A와 Candidate B를 승자/패자 방식으로 합치지 않고 서로 다른 책임으로 결합한다.

```text
Onboarding Starter Pack
        ↓
Customer / Project Input Contract
        ↓
Candidate A responsibility
Business Intake → 6W → RQ/FR/BR/AC → Customer View → Development Blueprint
        ↓
Candidate B responsibility
Evidence/Truth → Permission → Target Proof → Work Unit/Lane → Test/Verify/K1 Guard
        ↓
Brownfield Source Change
```

## Responsibility Boundary

### Starter Pack — 프로젝트 진입점
- 고객 문서 제공 가이드
- Business Source Manifest
- 용어집
- 산출물 선택표
- Source Profile
- Existing Source Analysis Guide
- SoP/Source/Change Skill
- 분석/Source Change Prompt

### Candidate A — 무엇을 만들어야 하는가
- Legacy Raw/Topic/RQ Boundary
- 6W Business Scenario
- RQ / FR / BR / AC
- Customer Functional Specification
- Process / Impact / Functional Design
- Development Blueprint
- UI / Field / CRUD / Logic / Integration / Query / Data / Common Code / Test 구조

### Candidate B — 지금 그것을 믿고 실행해도 되는가
- Truth: GIVEN / OBSERVED / INFERRED / CONFIRMED / OPEN
- Evidence revision / freshness / authority
- Stage quality / blind spot / assumption
- Action Permission
- Target Write Proof
- PGM Write Lane
- Work Unit / Idempotency / Recovery
- Verify / K1 Promotion Guard

## Canonical Combination Rule

A 문서를 B 문서로 교체하지 않는다. 동일 Subject ID를 공유하고 B Evidence/Permission을 Overlay한다.

```text
RQ-FLEX-PLAN-001
├ business-definition-6w.md              ← A meaning
├ customer-functional-spec.md            ← A customer view
├ development-blueprint.md               ← A engineering view
├ evidence-envelope.yaml/md              ← B evidence overlay
├ action-permission.yaml/md              ← B execution overlay
└ work-unit / verification evidence      ← B runtime overlay
```

## Core Rule

`Business Completeness != Execution Permission`

상세 업무정의와 Development Blueprint가 충분해도 Current Source revision, 공통코드, 권한/Profile, DB Key/Lock, Integration Contract, Test Evidence가 부족하면 실제 Source Write/Merge/Release는 제한할 수 있다.

## Main Policy

이 Branch는 통합 검증 Branch이며 `main`에 자동 병합하지 않는다. 기존 A/B/Starter Branch는 비교와 추적을 위해 보존한다.
