# P0/P1 Structural Redesign Contract v1

> Branch: `SDLC_DESIGN_SESSION_SECOND/p0-p1/structural-redesign-v1`  
> Base: `SDLC_DESIGN_SESSION_SECOND/p1/foundation-knowledge-bootstrap-v1`  
> Scope: P0 Safety Contract와 P1 Foundation을 유지하면서 사용자 진입점과 Runtime consumer 관계를 재구성한다.

## 1. 목적

기존 P0/P1의 문제는 Safety Contract 부족이 아니라 Bootstrap, Stage, Artifact Profile, Provider, Source Discovery, Reverse Sync가 분산되어 실제 사용자가 하나의 실행 흐름으로 소비하기 어렵다는 점이다.

이번 재설계는 기존 Safety를 삭제하지 않고 다음 실행 그래프를 만든다.

```text
Project Profile
→ Bootstrap Runtime
→ Artifact Profile Resolver
→ Stage Input Pack
→ Stage Execution Resolver
→ Command Context Builder
→ Provider Router
→ Provider Runtime
→ Output / Next Stage Pack
```

Brownfield Source는 별도로 다음 그래프를 사용한다.

```text
Bounded Inventory
→ Analyzer Selection
→ Bounded Trace
→ Source Change Evidence
→ Confirmed Reference Graph
→ Reverse Sync Candidate
```

## 2. 유지하는 P0/P1 Safety

다음은 구조 단순화 대상이 아니다.

- Human Truth와 Source Evidence 분리
- Candidate와 Canonical 분리
- OPEN Preservation
- Test Design Coverage와 Runtime PASS 분리
- Source Revision / File Hash
- Explicit Provider Capability Boundary
- Write Permission / Idempotency / Expected Revision
- UNKNOWN_AFTER_WRITE
- No implicit provider fallback
- Late-bound Overlay
- Source Behavior의 Business Truth 자동 승격 금지
- Representative Vertical Slice 전 Production/Scale-out 주장 금지

## 3. Redesign Decision

### D1. `/setup`을 Public Runtime Command에서 제거

초기화는 `bootstrap_project.py`의 deterministic bootstrap으로 분리한다.

Public Runtime Command는 계속 `/work /change /check`만 유지한다.

이유:
- Project Bootstrap은 일반 Stage 실행과 lifecycle이 다르다.
- Provider command router가 존재하지 않는 `/setup`을 문서상 지원하는 모순을 제거한다.

### D2. Stage Routing을 단일 Runtime Authority로 지정

Authority: `sdlc/config/stage-routing.yaml`

Stage는 다음을 직접 결정한다.

- Skill
- Required Capability
- Optional Capability
- Allowed Side-effect Action
- Output Artifact
- Next Stage

Caller/Agent가 Required Capability를 임의 구성하지 않는다.

### D3. OPEN을 Action-scoped Guard로 변경

기존 Command Runtime의 `open_items가 하나라도 있으면 ACTION_REQUIRED` 규칙을 폐기한다.

OPEN은 다음을 갖는다.

```yaml
blocks_reasoning: false
blocks_action: true
action_scopes: [source.write]
```

규칙:
- nonblocking OPEN → read-only progress 계속
- `blocks_reasoning=true` → 해당 reasoning 진행 불가
- `blocks_action=true` → 해당 `action_scopes`만 Guard
- Provider optional capability 부재 → PARTIAL/OPEN
- Provider required capability 부재 → dependent action ACTION_REQUIRED

### D4. Artifact Profile을 Runtime Consumer에 연결

Authority: `artifact-profiles.yaml`
Resolver: `resolve_artifact_profile.py`

Rule:
- MUST → 생성
- OFF → 생성하지 않음
- OPTIONAL/CONDITIONAL/CONDITIONAL_L2_ONLY/CONFIGURABLE_L1_L2 → 기본 비생성
- Conditional artifact가 필요한 경우 Stage Pack의 `execution.requested_outputs`로 명시

따라서 LITE는 내부 Safety/Trace를 유지하면서 Human-facing 문서를 실제로 줄인다.

### D5. Source Discovery를 Inventory와 Trace로 분리

초기 Brownfield Bootstrap에서 Direct Trace Manifest를 요구하지 않는다.

1. INVENTORY: 구조/언어/Build/Test/Data 후보 식별
2. ANALYZER_SELECTION: 필요한 language/framework/db/batch/interface Adapter 선택
3. BOUNDED_TRACE: 현재 Requirement에 필요한 범위만 추적

Core는 bounded inventory와 evidence envelope를 책임지고 language/framework parsing은 Adapter가 책임진다.

### D6. Reverse Sync에서 Pilot/Framework Heuristic 제거

Core Reverse Sync 입력은 `SOURCE_CHANGE_EVIDENCE`다.

Analyzer가 다음과 같은 generic signal을 제공한다.

- added_or_changed_branch_condition
- query_semantics_changed
- endpoint_contract_changed
- authorization_rule_changed

Core는 signal을 분류하고 Confirmed Reference Graph의 직접 관계만 따라간다.

- PGM/ART/SYMBOL/DATA/INT/TC → STALE_CANDIDATE 가능
- RQ/FR/BR/PROC/FTR/AC → REVIEW_CANDIDATE
- Human confirmed truth → overwrite 금지

기존 fixture-specific `build_reverse_sync_candidate.py`는 `DEPRECATED_REFERENCE_ONLY`로 유지한다.

## 4. Greenfield Bootstrap

Greenfield에서 Source Provider는 시작 필수조건이 아니다.

미확정 항목:
- Language
- Framework
- DB
- Deployment
- Architecture
- Coding/Naming
- Logging/Error
- Security
- Test
- CI/CD
- Document Rule

은 모두 OPEN Decision으로 시작한다.

Agent는 Candidate를 만들 수 있으나 자동 CONFIRMED하지 않는다.

## 5. Brownfield Bootstrap

AUTO Mode는 bounded marker evidence로 Brownfield 후보를 결정한다.

초기 inventory는 전체 source content를 읽거나 무제한 recursive scan하지 않는다.

Source Provider가 UNCONFIGURED여도 Project Bootstrap 자체는 가능하다. 다만 Source claim 관련 capability만 Guard한다.

## 6. Stage Input Pack v1.3

추가된 핵심 필드:

```yaml
metadata:
  project_mode: AUTO
execution:
  requested_actions: []
  requested_outputs: []
  capability_inputs: {}
  write_proofs: {}
  human_actions: []
  adapter_configs: {}
```

Stage Pack은 대화 History 없이 다음 실행 Plan을 만들 수 있는 실행 Entry다.

## 7. Write Boundary

Side-effect Action은 Stage가 허용하고 Stage Pack이 명시적으로 요청한 경우에만 Runtime Capability에 포함한다.

Write에는 capability별 다음 proof가 필요하다.

```yaml
expected_revision:
idempotency_key:
permission_proof_ref:
```

없는 proof는 Human Action blocker로 변환한다.

## 8. Fast Toolkit

LITE/Standard/Enterprise는 Stage의 존재 여부보다 Human Artifact emission을 우선 조절한다.

Internal Trace/Safety를 문서 수와 1:1로 만들지 않는다.

LITE 예:

```text
Requirement Customer View
Engineering Design
Implementation Result
Test/Verification
Worklist
```

Process/Impact/Program Detail은 필요할 때만 requested_outputs로 활성화한다.

## 9. Provider Extension Boundary

기존 P0.6~P0.9 Provider Protocol은 유지한다.

새 Provider가 기존 Capability를 구현하면 필요한 변경은 원칙적으로:

```text
Adapter
+ Provider Registry Entry
```

새 Capability가 필요한 경우:

```text
Adapter
+ Registry
+ Stage Capability Mapping
```

Core SDLC 문서 자체의 수정은 필요하지 않아야 한다.

## 10. 아직 해결하지 않은 항목

이번 v1 범위에서 다음은 완료로 주장하지 않는다.

- XLSX Requirement 직접 Intake Adapter
- 전체작업목록 MD↔XLSX 실제 양방향 Runtime
- 설치/배포용 독립 package installer
- 실제 Java/Spring Analyzer 연결
- 실제 SQL/Procedure/Trigger Analyzer
- 실제 Batch/Scheduler Analyzer
- 실제 Interface Analyzer
- 실제 Source write Provider
- 실제 Canonical Registry Provider
- Multi-Agent branch/file ownership runtime enforcement
- 모든 Stage의 artifact generator 완성
- 실제 고객 Source Vertical Slice PASS
- CI PASS
- Production Ready

## 11. Validation Contract

Self-test: `sdlc/scripts/test_structural_redesign.py`

검증 대상:
- LITE Conditional artifact suppression
- nonblocking OPEN progress
- action-scoped write guard
- optional provider missing → PARTIAL
- required provider missing → ACTION_REQUIRED
- Greenfield/Brownfield AUTO bootstrap
- analyzer-neutral confirmed-trace reverse sync

CI 정의: `.github/workflows/structural-redesign-selftest.yml`

CI run이 실제로 존재하지 않으면 PASS로 간주하지 않는다.

## 12. 상태

현재 목표 상태:

```text
P0 Safety = PRESERVED
P1 Foundation = PRESERVED
Bootstrap Runtime = IMPLEMENTED_V1
Stage Routing Consumer = IMPLEMENTED_V1
OPEN Action Scope = IMPLEMENTED_V1
Artifact Profile Consumer = IMPLEMENTED_V1
Generic Source Inventory = IMPLEMENTED_V1
Generic Reverse Sync Core = IMPLEMENTED_V1
Real Analyzer Adapters = NOT IMPLEMENTED
Real Project Vertical Slice = NOT RUN
Production Ready = false
```
