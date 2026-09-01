# P0 Final Design Baseline Exit Result

> Branch: `SDLC_DESIGN_SESSION_SECOND/p0.final/design-baseline-exit-v1`  
> Scope: P0 Design Baseline / Safety Contracts / Runtime Boundary  
> Important: 첨부 요구사항목록 및 근태 Pilot은 회귀/샘플이며 P0 Exit의 필수 입력이 아니다.

## 1. Final Verdict

**P0 DESIGN BASELINE: READY FOR P1**

Machine state:

`P0_BASELINE_READY`

Production Ready:

`false`

P0 완료는 실제 고객 시스템의 운영 준비 완료가 아니다. P0에서는 P1 이후 구현을 시작할 수 있을 만큼 Harness의 구조, Truth 경계, Handoff, Provider/Runtime 계약, 실패/복구 정책이 고정되었는지를 판정한다.

## 2. P0 전체 완료 범위

| 영역 | 결과 |
|---|---|
| Artifact/Profile simplification | BASELINED |
| Legacy Requirement Normalization | BASELINED |
| RQ Boundary / Human Review Gate | BASELINED |
| Canonical Publish Safety | BASELINED |
| Stage Input Pack / Low-Agent Handoff | BASELINED |
| Brownfield Source Discovery | BASELINED |
| Source Reverse Sync | BASELINED |
| Test Contract / Verification Gate | BASELINED |
| E2E Status / Blocker Orchestration | BASELINED |
| Provider Capability Boundary | BASELINED |
| Reference Adapter / Conformance Harness | BASELINED |
| Runtime Invocation / Retry / Recovery | BASELINED |
| `/work /change /check` Runtime Integration | BASELINED |
| P0 Exit Gate | BASELINED |

## 3. Original Phase 0 역할과 현재 구조

초기 설계의 논리적 `manifest.yaml`, `capabilities.yaml`, `decisions.yaml`, `contracts/` 역할을 그대로 복제하는 별도 Truth 파일을 새로 만들지 않았다.

대신 `sdlc/config/baseline-contract-index.yaml`이 현재 authoritative artifact를 가리킨다.

- Manifest 역할 → Business Source Manifest + Project/Profile authorities
- Capabilities 역할 → Provider Capability Registry
- Decisions 역할 → Requirement Review / RQ Boundary / Canonical Publish typed artifacts
- Contracts 역할 → `sdlc/design/contracts/`의 분산 계약

Index 자체는 업무/설계 Truth의 사본이 아니며 `duplicate_truth_in_index: DENY`다.

## 4. Critical Safety Gates

### Candidate / Canonical

Canonical Publish는 Human/L2가 Boundary/Decision을 `CONFIRMED`하고 Evidence/Revision/Source Coverage 및 사전 할당 Canonical ID가 있어야 한다.

다음은 금지된다.
- Candidate Hash에서 Canonical ID 자동 생성
- Candidate ID를 Canonical ID로 재사용
- OPEN/PROVISIONAL 상태 Publish

### Source / Business Truth

Source/Test Provider Evidence는 관찰 Evidence이며 Business Truth를 자동 `CONFIRMED`하지 않는다. Reverse Sync는 Technical Artifact를 STALE Candidate로 올릴 수 있지만 Requirement/Business Rule은 Review Candidate로 보호한다.

### Test / Verify

AC↔TC 설계 Coverage와 Runtime PASS를 분리한다. `VERIFIED_PASS`는 실제 Runtime, 모든 필수 TC PASS, 실행 Evidence, Source Evidence Set 일치, blocker 해소, Business Rule 검토, Production Source를 요구한다.

### Provider Defaults

기본 Example Registry:
- SOURCE = `UNCONFIGURED`
- TEST = `UNCONFIGURED`
- CANONICAL_REGISTRY = `DISABLED`
- COMMAND_ROUTER = `AVAILABLE`

예제 파일의 존재만으로 실제 Tool 연결을 주장할 수 없다.

### Write Recovery

- Read: Provider가 `retryable=true`라고 명시한 경우에만 제한 재시도
- Write: 자동 재시도 비활성
- Write dispatch 이후 response loss/exception → `UNKNOWN_AFTER_WRITE`
- Recovery Evidence 없이 성공/실패를 추측하지 않음

## 5. Command Runtime

사용자 Surface는 계속 다음 세 개를 유지한다.

- `/work`
- `/change`
- `/check`

Command Runtime은 명령 이름을 특정 Adapter에 직접 연결하지 않는다.

```text
Command
→ Required Capability
→ Provider Registry
→ Provider Request
→ Invocation Journal
→ Provider Response
→ Command Runtime Result
```

결과 상태:
- COMPLETE
- PARTIAL
- ACTION_REQUIRED
- RECOVERY_REQUIRED
- INVALID

`UNKNOWN_AFTER_WRITE`가 하나라도 있으면 `RECOVERY_REQUIRED`다.

## 6. Anti-overfitting

P0.6~P0.9의 Core Contract/Adapter/Runtime에는 Pilot-specific 값을 넣지 않도록 Guard를 정의했다.

Forbidden regression tokens:
- `REQ_TM_TE`
- `RQG-CAND-6BB6D66548`
- `근태`
- `AttendanceClose`
- `TB_ATT_`
- `10분`

첨부 요구사항목록은 Normalizer/Review 파일럿과 Regression 검증에는 사용되었지만 P0 Exit Gate의 required input은 아니다.

Provider/Adapter 검증은 별도의 generic Greenfield/Brownfield, Python/FastAPI, TypeScript/event, local filesystem/subprocess fixture 등으로 분리했다.

## 7. Greenfield / Brownfield 적용성

### Greenfield
Existing Source가 없는 초기 Requirement/Design은 정상 상태로 허용한다. Source Provider 부재를 무조건 실패로 만들지 않는다.

### Brownfield
Discovery/Impact에 Source Evidence가 필요한 Stage만 필요한 Source Capability를 명시적으로 요청한다. Provider가 없거나 UNCONFIGURED이면 OPEN/ACTION_REQUIRED로 유지한다.

### Hybrid
Work Unit별 Existing/New 영역이 요구하는 Capability를 기준으로 판단한다.

## 8. Low-Agent

저수준 Agent가 기계적으로 처리할 수 있는 범위:
- ID/Required Field/Reference 검증
- Legacy Grouping
- Candidate Review Queue
- Stage Pack Handoff
- Provider Capability Matching
- Request/Response Correlation
- Adapter Conformance
- Invocation Journal/Retry 상태
- E2E Blocker 집계
- Exit Gate 구조검증

L2/Human이 유지되는 범위:
- Requirement Business Boundary
- Business Rule 의미 확정
- Canonical Publish 승인
- Production 수용/Release 결정

Engineering/L3 범위:
- 실제 Provider Adapter 연결
- Runtime/DB/Procedure/Distributed dependency
- credential/permission/security
- UNKNOWN_AFTER_WRITE 복구

## 9. P0 Exit Validation Basis

이번 최종 판정은 다음에 근거한다.

1. GitHub final branch recursive tree를 통해 P0.1~P0.9 Core/Contract/Test definition과 P0 Exit 파일의 구조적 존재를 확인했다.
2. Critical Config를 직접 확인했다.
   - Provider Source/Test default `UNCONFIGURED`
   - Write retry false / UNKNOWN_AFTER_WRITE
   - Baseline index duplicate truth DENY
   - Canonical Human/L2 Publish Gate
   - Runtime-only VERIFIED_PASS Gate
3. P0.8/P0.9/Exit에 generic self-test definitions를 추가했다.

현재 세션 실행환경에서 `github.com` DNS를 해석하지 못해 final branch를 별도 checkout하여 Repository의 Python self-test 전체를 실행하지는 못했다.

따라서 다음은 주장하지 않는다.
- repository checkout 기반 P0 전체 test suite PASS
- CI PASS
- 실제 고객 Provider PASS
- Production Ready

## 10. External Non-P0 Blockers

P0 Design Baseline Exit 자체를 막지는 않지만 실제 고객 프로젝트/Production에는 다음이 필요하다.

1. 실제 고객 Source Repository/Snapshot
2. 실제 프로젝트 Runtime 및 Test Command
3. Production Provider credential/permission
4. 실제 Canonical Registry/ID Provider 구현
5. 프로젝트별 Human Requirement Boundary Decision
6. Runtime/DB/Batch/Procedure/Integration 검증
7. Production Verification / Release 승인

## 11. P0 Exit State

```text
P0_BASELINE_READY
Production Ready = false
Sample/Pilot required for Exit = false
Next Phase = P1
```

## 12. P1 Entry Recommendation

다음 단계는 `P1 Foundation / Knowledge Bootstrap`이다.

P1에서는 P0 계약을 다시 설계하지 않고 다음을 구현 대상으로 삼는다.
- Foundation/Knowledge bootstrap
- Artifact/Reference graph validation
- Glossary/reference lint
- Knowledge source bootstrap/provenance
- OPEN_ITEM blocking mode runtime
- Baseline artifact cache/index
- 실제 Provider Adapter를 Project Overlay로 연결하는 onboarding path

P1도 `SDLC_DESIGN_SESSION_SECOND/` 하위 별도 Branch에서 진행하고 `main`에는 병합하지 않는다.
