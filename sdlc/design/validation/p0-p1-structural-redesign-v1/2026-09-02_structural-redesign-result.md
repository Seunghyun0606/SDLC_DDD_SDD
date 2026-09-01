# P0/P1 Structural Redesign v1 Validation Result

> Branch: `SDLC_DESIGN_SESSION_SECOND/p0-p1/structural-redesign-v1`  
> Base: `SDLC_DESIGN_SESSION_SECOND/p1/foundation-knowledge-bootstrap-v1`  
> Validated runtime head: `a681c55f5aa0adb38a71d8a4c0f5f323e2f88157`  
> GitHub Actions Run: `33550746736`  
> Date: 2026-09-02

## Verdict

**STRUCTURAL REDESIGN V1: IMPLEMENTED AND SELF-TESTED**

Machine state:

`P0_P1_STRUCTURAL_REDESIGN_V1_SELFTEST_PASS`

Production Ready: `false`

이 결과는 P0/P1 Safety Contract를 유지하면서 Bootstrap/Stage Routing/Artifact Profile/Open Guard/Source Discovery/Reverse Sync의 구조적 공백을 v1 수준에서 연결했다는 의미다. 실제 고객 Source Vertical Slice 또는 Production Ready를 의미하지 않는다.

## 1. Preserved Safety

다음 P0/P1 Safety는 유지했다.

- Human Truth != Source Evidence
- Candidate != Canonical
- OPEN Preservation
- Test Design Coverage != Runtime PASS
- Source Revision / Hash
- Provider Capability Boundary
- No implicit fallback
- Permission / Expected Revision / Idempotency proof
- UNKNOWN_AFTER_WRITE
- Write automatic retry 금지
- Late-bound Overlay
- Source Behavior의 Business Truth 자동 승격 금지
- Representative Vertical Slice 이전 Production/Scale-out 주장 금지

## 2. Implemented Structural Changes

### 2.1 Bootstrap Runtime

Added:
- `sdlc/config/bootstrap-runtime.yaml`
- `sdlc/scripts/bootstrap_project.py`
- `sdlc/templates/project-profile-user.yaml`

Behavior:
- `/setup`을 존재하지 않는 Public Runtime Command로 취급하지 않는다.
- Bootstrap은 별도 deterministic entry point다.
- AUTO는 bounded marker evidence만 사용해 Greenfield/Brownfield 후보를 결정한다.
- Greenfield 기술 선택은 OPEN Decision으로 남긴다.
- Brownfield Source Provider 부재는 Source 관련 Action만 Guard한다.

### 2.2 Stage → Capability Runtime Routing

Added:
- `sdlc/config/stage-routing.yaml`
- `sdlc/scripts/resolve_stage_execution.py`
- `sdlc/scripts/build_command_context.py`

Behavior:
- Stage가 Skill/Required Capability/Optional Capability/Output/Next Stage를 결정한다.
- Caller/Agent가 Required Capability를 임의 구성하지 않는다.
- Side-effect capability는 `execution.requested_actions`에 명시된 경우에만 Required가 된다.
- `test.execute`도 TEST Stage 진입만으로 실행되지 않는다.

### 2.3 OPEN Action Scope

Updated:
- `sdlc/templates/open-item.yaml`
- `sdlc/scripts/evaluate_open_items.py`
- `sdlc/scripts/route_provider_command.py`
- `sdlc/scripts/execute_command_runtime.py`

Canonical OPEN shape:

```yaml
open_id:
blocks_reasoning:
blocks_action:
action_scopes: []
required_evidence: []
escalation:
```

Behavior:
- nonblocking OPEN은 Read/Analysis 진행을 막지 않는다.
- Required Provider가 없으면 dependent capability/action만 Guard한다.
- Optional Provider가 없으면 PARTIAL/OPEN으로 유지한다.
- Guard된 capability 외 독립 capability는 계속 실행할 수 있다.
- 기존 `open_item_id`, `blocks_side_effecting_action`은 evaluator compatibility read만 지원한다.

### 2.4 Artifact Profile Runtime Consumer

Added:
- `sdlc/scripts/resolve_artifact_profile.py`

Behavior:
- `MUST` → 생성 대상
- `OFF` → 비생성
- `OPTIONAL/CONDITIONAL/CONDITIONAL_L2_ONLY/CONFIGURABLE_L1_L2` → 기본 비생성
- 필요할 때 Stage Pack의 `execution.requested_outputs`로 opt-in

이로써 LITE가 Config 선언만 존재하는 상태에서 실제 Human Artifact 감소 동작으로 연결됐다.

### 2.5 Generic Source Discovery

Added/Updated:
- `sdlc/config/source-discovery.yaml`
- `sdlc/config/source-analyzers.yaml`
- `sdlc/scripts/discover_source_inventory.py`
- `sdlc/scripts/collect_bounded_source_evidence.py`
- `sdlc/templates/source-target-context.yaml`

Flow:

```text
INVENTORY
→ ANALYZER_SELECTION
→ BOUNDED_TRACE
```

Initial Inventory는 Direct Trace Manifest를 요구하지 않는다.

Core 책임:
- bounded inventory
- explicit path/hash
- evidence envelope
- revision/hash
- OPEN preservation

Adapter 책임:
- Java/Spring
- SQL/Procedure/Trigger
- Batch/Scheduler
- Interface
- Runtime dependency

기존 `discover_source_evidence.py`는 `DEPRECATED_REFERENCE_ONLY`로 남겼다.

### 2.6 Generic Reverse Sync

Added/Updated:
- `sdlc/templates/source-change-evidence.yaml`
- `sdlc/scripts/build_reverse_sync_from_signals.py`
- `sdlc/config/reverse-sync-classification.yaml`

Behavior:
- Core는 특정 Java Class/근태/상수/시간값을 해석하지 않는다.
- Analyzer가 generic semantic signal을 생성한다.
- 자동 STALE 전파는 Confirmed Reference Graph의 직접 relation만 사용한다.
- PGM/ART/SYMBOL/DATA/INT/TC → STALE_CANDIDATE 가능
- RQ/FR/BR/PROC/FTR/AC → REVIEW_CANDIDATE
- Human Confirmed Truth는 보호한다.

기존 `build_reverse_sync_candidate.py`는 `DEPRECATED_REFERENCE_ONLY`다.

### 2.7 Quick Start

Updated/Added:
- `sdlc/README.md`
- `sdlc/starter/prompts/greenfield-first-prompt.md`
- `sdlc/starter/prompts/brownfield-first-prompt.md`
- `sdlc/scripts/create_initial_stage_pack.py`

Reference flow:

```text
ai-sdlc.yaml
→ Bootstrap
→ Artifact Profile Resolve
→ Greenfield/Brownfield First Prompt
→ Initial Stage Pack
→ Stage Execution Plan
→ Command Context
→ /work Runtime
```

## 3. Contract Consistency Fixes

이번 재설계 중 기존 P1과의 구조적 불일치도 수정했다.

- `reference-graph.yaml`의 `nodes/edges`를 P1 Validator가 실제 읽는 `reference_graph` 내부로 이동
- Bootstrap Result가 기존 P1 Validator의 `mode/providers/customization` shape를 계속 만족하도록 호환 유지
- `command-runtime-context.yaml`을 Stage Bridge가 실제 생성하는 schema_version 2와 일치시킴
- `project-profile.example.yaml`의 declarative key를 실제 Runtime consumer path에 연결
- `baseline-contract-index.yaml`은 Truth를 복제하지 않고 실제 consumer path만 index

## 4. CI Evidence

Workflow:

`.github/workflows/structural-redesign-selftest.yml`

GitHub Actions Run:

`33550746736`

Validated Head:

`a681c55f5aa0adb38a71d8a4c0f5f323e2f88157`

Result:

```text
Set up job                         SUCCESS
Checkout                           SUCCESS
Setup Python                       SUCCESS
Install PyYAML                     SUCCESS
Compile redesigned runtime         SUCCESS
Run P1 compatibility tests         SUCCESS
Run structural redesign tests      SUCCESS
Overall                            SUCCESS
```

## 5. Structural Self-test Coverage

`test_structural_redesign.py`가 다음을 검증한다.

1. LITE Conditional Artifact default suppression
2. Conditional Artifact explicit opt-in
3. nonblocking OPEN progress
4. action-scoped Side-effect Guard
5. Write proof 누락 → Human Action blocker
6. Optional Provider missing → PARTIAL
7. Required Provider missing → ACTION_REQUIRED
8. AUTO Greenfield/Brownfield Bootstrap
9. Redesigned Bootstrap의 기존 P1 Validator 호환
10. Generic bounded source evidence
11. Generic confirmed-trace reverse sync
12. Reference Graph Template shape
13. Canonical OPEN Template shape
14. TEST Stage의 explicit `test.execute`
15. Project Profile의 Runtime consumer path 존재
16. Active Core의 Pilot token leakage 금지

Forbidden Active-Core regression tokens:

- `REQ_TM_TE`
- `RQG-CAND-6BB6D66548`
- `AttendanceClose`
- `ATT-CLOSE`
- `FORCE_CLOSE`
- `TB_ATT_`
- `10분`

## 6. Current Limitations / Not Yet Implemented

다음은 이번 v1에서 해결 완료로 주장하지 않는다.

### P0/P1 next implementation

- XLSX Requirement direct Intake Adapter
- `전체작업목록.md ↔ .xlsx` 실제 Canonical Import/Export Runtime
- 독립 package installer / distribution
- 실제 Java/Spring Analyzer Adapter
- 실제 SQL/Procedure/Trigger Analyzer Adapter
- 실제 Batch/Scheduler Analyzer Adapter
- 실제 Interface Analyzer Adapter
- 실제 Source Write Provider
- 실제 Canonical Registry Provider
- 모든 Stage별 Artifact Generator
- Generic E2E Status Orchestrator 재구성
- Multi-Agent branch/file ownership Runtime enforcement
- Semantic document merge runtime

### Real Project Validation

아직 수행하지 않음:

- 실제 고객 Source 연결
- 첨부 요구사항목록의 새로운 구조 전체 Vertical Slice 재실행
- 실제 Build/Test Command 실행
- 실제 DB/Procedure/Batch/Interface Provider 검증
- 실제 Source write/recovery
- Production Verification

## 7. Readiness State

```text
P0 Safety Contract                         PRESERVED
P1 Foundation                              PRESERVED
P1 Compatibility CI                        PASS
Bootstrap Runtime v1                       PASS_SELFTEST
Stage Routing Consumer v1                  PASS_SELFTEST
OPEN Action-scoped Runtime                 PASS_SELFTEST
Artifact Profile Runtime                   PASS_SELFTEST
Generic Source Inventory/Bounded Trace     PASS_SELFTEST
Generic Reverse Sync Core                  PASS_SELFTEST
Real Analyzer Adapters                     NOT_IMPLEMENTED
Generic E2E Orchestrator                    NOT_YET_REDESIGNED
Real Customer Vertical Slice               NOT_RUN
Production Ready                           false
```

## Final Decision

현재 재설계 Branch는 **P0/P1의 안전 구조를 버리지 않고, 가장 큰 실행 공백이었던 Bootstrap → Stage → Capability → Runtime과 Profile/Source/Reverse Sync consumer 연결을 실제 코드로 보완한 상태**다.

다음 우선순위는 새로운 Core 재설계가 아니라 다음 Representative Vertical Slice를 위한 Adapter/Intake 구현이다.

1. XLSX Requirement Intake
2. Generic E2E Orchestration
3. Java/Spring + SQL/DB Representative Analyzer
4. 첨부 요구사항 중 대표 RQ 1건 End-to-End 실행
5. Multi-Agent Branch/Revision Guard
