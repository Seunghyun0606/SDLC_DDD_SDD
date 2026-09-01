# AI-SDLC Harness Quick Start

> 현재 구조는 P0 Safety Contract + P1 Foundation + Structural Redesign v1 위에 P2의 XLSX Intake, Generic Analyzer, E2E Read Model, Revision/Ownership Guard를 연결한 상태다.

## 1. 사용자가 기억할 명령

일반 진행 명령은 세 가지다.

- 진행: `/work <RQ/PGM/TASK>` 또는 자연어로 계속 진행
- 변경: `/change` 또는 변경 내용 입력
- 조회: `/check <ID>`

`/setup`은 Runtime Command가 아니다. 초기화는 `bootstrap_project.py`가 담당한다.

OPEN이 있다는 이유만으로 전체 Workflow를 멈추지 않는다. `blocks_reasoning=true` 또는 특정 `action_scopes`에 `blocks_action=true`인 경우에만 해당 Reasoning/Action을 Guard한다.

## 2. 프로젝트 최소 파일

Packaging/Installer가 별도로 제공되기 전 Reference 배치는 Project Repository에 `sdlc/`을 포함하는 Embedded 방식이다.

```text
ai-sdlc.yaml        # 사용자 설정
.ai-sdlc/           # Runtime 생성 상태/Plan/Stage Pack
requirements.xlsx   # 선택: 고객 Requirement Source
```

P0/P1/P2 내부 Validation 문서는 일반 프로젝트 참여자가 직접 수정하지 않는다.

## 3. 프로젝트 설정

```bash
cp sdlc/templates/project-profile-user.yaml ai-sdlc.yaml
mkdir -p .ai-sdlc
```

최소 설정:

```yaml
project:
  name: my-project
  mode: AUTO
artifacts:
  profile: STANDARD
```

Mode: `AUTO | GREENFIELD | BROWNFIELD | HYBRID`

Profile: `LITE | STANDARD | ENTERPRISE`

## 4. Bootstrap

```bash
python sdlc/scripts/bootstrap_project.py \
  . \
  ai-sdlc.yaml \
  sdlc/config/provider-registry.example.yaml \
  -o .ai-sdlc/project-bootstrap.yaml
```

Bootstrap은 Repository 전체를 무제한 Scan하지 않는다.

- 기존 Source/Build marker 없음 → GREENFIELD 후보
- 기존 Source/Build marker 있음 → BROWNFIELD 후보
- Source Provider 미연결 → Source 관련 Action만 Guard
- Greenfield 기술 Stack 미정 → OPEN Decision 유지

## 5. XLSX Requirement 직접 Intake

고객 Requirement가 Excel이면 별도 YAML 수작업 변환 없이 직접 Intake한다.

```bash
python sdlc/scripts/intake_requirements_xlsx.py \
  requirements.xlsx \
  --only-id REQ-001 \
  -o .ai-sdlc/requirement-intake.yaml
```

Core는 고정 Column 위치를 요구하지 않고 Header Alias를 탐색한다. 프로젝트별 Header 차이는 `sdlc/config/requirement-intake.yaml` 또는 Overlay에서 확장한다.

Intake 결과의 Workbook 값은 `GIVEN Source Requirement`다.

- Source Row/Worksheet/File Hash를 보존
- Canonical RQ/FR ID를 자동 생성하지 않음
- 빈 Cell을 추측해서 채우지 않음

## 6. Artifact Profile

```bash
python sdlc/scripts/resolve_artifact_profile.py \
  sdlc/config/artifact-profiles.yaml \
  ai-sdlc.yaml \
  -o .ai-sdlc/artifact-plan.yaml
```

- `MUST` → 생성
- `OFF` → 생성하지 않음
- `OPTIONAL / CONDITIONAL / CONDITIONAL_L2_ONLY / CONFIGURABLE_L1_L2` → 기본 비생성, 필요할 때 `execution.requested_outputs`로 요청

LITE에서도 Canonical Trace/OPEN/Revision/Evidence Safety는 유지한다.

## 7. Greenfield / Brownfield 첫 Prompt

Bootstrap `resolved_mode`에 따라 사용한다.

- Greenfield: `starter/prompts/greenfield-first-prompt.md`
- Brownfield: `starter/prompts/brownfield-first-prompt.md`

Greenfield 기술 선택을 AI가 임의 확정하지 않으며 Brownfield Source Behavior도 Business Truth로 승격하지 않는다.

## 8. Brownfield Source Inventory

```bash
python sdlc/scripts/discover_source_inventory.py \
  . \
  <SOURCE_REVISION> \
  -o .ai-sdlc/source-inventory.yaml
```

Inventory는 Business 관계를 확정하지 않는다. 식별된 실제 파일만 Analyzer에 전달한다.

현재 제공 Adapter:

- Java/Spring: `sdlc/scripts/analyze_java_spring.py`
- SQL/Database: `sdlc/scripts/analyze_sql_database.py`

예:

```bash
python sdlc/scripts/analyze_java_spring.py . \
  --file src/main/java/example/ExampleController.java \
  -o .ai-sdlc/java-analysis.yaml
```

```bash
python sdlc/scripts/analyze_sql_database.py . \
  --file db/schema.sql \
  -o .ai-sdlc/sql-analysis.yaml
```

Analyzer는 명시된 파일만 분석하며 출력은 `OBSERVED`다. Name Similarity만으로 Confirmed Trace를 만들지 않는다.

Batch/Scheduler/Interface Adapter가 없으면 OPEN으로 남긴다.

## 9. Requirement → Stage Input Pack

고객 Requirement ID는 Source ID 그대로 유지한다.

```bash
python sdlc/scripts/create_initial_stage_pack.py \
  .ai-sdlc/project-bootstrap.yaml \
  <SOURCE_REQUIREMENT_ID> \
  <SOURCE_REVISION_OR_NO_SOURCE> \
  -o .ai-sdlc/intake-pack.yaml
```

Candidate ID는 Canonical ID가 아니다.

## 10. Stage Pack → 실행 Plan

```bash
python sdlc/scripts/resolve_stage_execution.py \
  sdlc/config/stage-routing.yaml \
  .ai-sdlc/intake-pack.yaml \
  --artifact-plan .ai-sdlc/artifact-plan.yaml \
  -o .ai-sdlc/stage-execution.yaml
```

Stage Router가 Skill, Required/Optional Capability, Output, Next Stage를 결정한다. Caller/Agent가 Required Capability를 임의로 조립하지 않는다.

부작용 Action은 `execution.requested_actions`에 명시된 경우에만 활성화한다.

## 11. Source Write 전 Revision / Ownership Guard

Multi-Agent Source 변경은 Write Proof 외에 Revision/Ownership Guard를 통과해야 한다.

```bash
cp sdlc/templates/change-execution-context.yaml .ai-sdlc/change-execution.yaml
python sdlc/scripts/guard_revision_ownership.py \
  .ai-sdlc/change-execution.yaml \
  -o .ai-sdlc/revision-ownership-guard.yaml
```

Guard 조건:

- `expected_revision == current_revision`
- Agent Branch / Parent Change Branch 존재
- 요청 File이 owned/shared path에 포함
- Shared File이면 coordination proof 필요
- 다른 Agent Active Claim과 겹치면 DENY

`source.write`를 요청하는 Stage Pack에는 Guard의 `decision: ALLOW`와 `guard_proof_ref`를 전달한다.

## 12. Provider Runtime Context

```bash
python sdlc/scripts/build_command_context.py \
  .ai-sdlc/intake-pack.yaml \
  .ai-sdlc/stage-execution.yaml \
  --command /work \
  -o .ai-sdlc/command-context.yaml
```

Write Action에는 다음이 필요하다.

- `expected_revision`
- `idempotency_key`
- `permission_proof_ref`
- Source Write이면 Revision/Ownership Guard `ALLOW`

실행:

```bash
python sdlc/scripts/execute_command_runtime.py \
  sdlc/config/provider-registry.example.yaml \
  .ai-sdlc/command-context.yaml \
  -o .ai-sdlc/command-result.yaml
```

Unavailable Required Capability는 그 Action을 Guard하고, 독립적인 다른 Capability는 계속 실행할 수 있다.

## 13. Source 변경 후 Reverse Sync

```bash
python sdlc/scripts/build_reverse_sync_from_signals.py \
  <SOURCE_CHANGE_EVIDENCE> \
  <REFERENCE_GRAPH> \
  sdlc/config/reverse-sync-classification.yaml \
  -o .ai-sdlc/reverse-sync-candidate.yaml
```

자동 STALE 전파는 `CONFIRMED Reference Graph` 직접 관계만 사용한다. RQ/FR/BR/PROC/FTR/AC는 Source 변경으로 자동 overwrite하지 않는다.

## 14. Generic /check E2E 상태

Stage 결과를 `e2e-execution-ledger.yaml` 형식으로 기록한 뒤 Domain-neutral Orchestrator를 실행한다.

```bash
python sdlc/scripts/orchestrate_generic_e2e_status.py \
  .ai-sdlc/e2e-ledger.yaml \
  -o .ai-sdlc/e2e-status.yaml
```

Release Ready는 다음을 모두 만족해야 한다.

- 모든 `required_for_release` Stage `COMPLETE`
- `blocks_release=true` Blocker 없음
- Verification `VERIFIED_PASS`
- `production_verified=true`

## 15. 역할별 시작점

| 역할 | 먼저 볼 것 | 주 동작 |
|---|---|---|
| PM | `docs/00_관리/전체작업목록.md` | `/check`, 우선순위/담당/일정 |
| BA/분석 | Requirement Intake + Stage Pack | `/work <ID>` |
| 설계/개발 | Design/PGM/TASK + Stage Pack | `/work <TASK>` |
| 테스트 | AC/TC + Runtime Evidence | `/work`, `/check` |
| Harness 관리자 | `ai-sdlc.yaml`, Provider/Overlay | Bootstrap/Provider 연결 |

## 16. Safety Invariants

Profile/Customization과 무관하게 제거하지 않는다.

- Human Truth != Source Evidence
- Candidate != Canonical
- Test Design Coverage != Runtime PASS
- OPEN Preservation
- UNKNOWN_AFTER_WRITE
- Side-effect Guard
- Revision/Hash
- Provider Capability Boundary
- Confirmed Trace Only Reverse Sync
- Revision Mismatch Auto-overwrite DENY
- Shared File Coordination Required

## 17. 검증

Structural Redesign:

```bash
python sdlc/scripts/test_structural_redesign.py
```

P2 Representative Slice:

```bash
python sdlc/scripts/test_p2_representative_slice.py
```

CI:

- `.github/workflows/structural-redesign-selftest.yml`
- `.github/workflows/p2-representative-slice-selftest.yml`

CI가 실제 실행되지 않았다면 PASS로 간주하지 않는다.

## 상세 문서

- `guides/01_SDLC_전체가이드.md`
- `guides/02_SKILL_사용가이드.md`
- `guides/03_TEMPLATE_산출물가이드.md`
- `guides/04_HARNESS_커스터마이징가이드.md`
- `design/contracts/p0-p1-structural-redesign-v1.md`
- `design/contracts/p2-representative-brownfield-slice-v1.md`
