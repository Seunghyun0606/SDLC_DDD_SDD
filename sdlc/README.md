# AI-SDLC Harness Quick Start

> 현재 구조는 P0 Safety Contract와 P1 Foundation을 유지하면서 Bootstrap → Stage Routing → Provider Runtime을 실제 소비 관계로 연결한 Structural Redesign v1 기준이다.

## 1. 사용자가 알아야 하는 것

일반 사용자의 진행 명령은 세 가지다.

- 진행: `/work <RQ/PGM/TASK>` 또는 자연어로 계속 진행
- 변경: `/change` 또는 변경 내용 입력
- 조회: `/check <ID>`

`/setup`은 Runtime Command가 아니다. 프로젝트 초기화는 `bootstrap_project.py`가 담당한다.

미확정 정보가 있다는 이유만으로 전체 Workflow를 정지하지 않는다. `blocks_reasoning=true` 또는 특정 `action_scopes`에 대해 `blocks_action=true`인 경우에만 해당 Reasoning/Action을 Guard한다.

## 2. 현재 배치 계약

Packaging/Installer가 별도로 제공되기 전까지 Reference 배치는 **Project Repository에 `sdlc/` 디렉터리를 포함하는 Embedded 방식**이다.

최소 사용자 관리 파일은 다음 두 종류다.

```text
ai-sdlc.yaml        # 프로젝트 이름/Mode/Profile
.ai-sdlc/           # Runtime이 생성하는 Bootstrap/Plan/Stage Pack
```

`design/validation`, P0/P1 내부 계약과 Self-test 결과는 일반 프로젝트 참여자가 직접 편집하지 않는다.

## 3. 최초 설정

```bash
cp sdlc/templates/project-profile-user.yaml ai-sdlc.yaml
mkdir -p .ai-sdlc
```

`ai-sdlc.yaml`에서 최소 다음만 정한다.

```yaml
project:
  name: my-project
  mode: AUTO
artifacts:
  profile: STANDARD
```

Mode는 `AUTO | GREENFIELD | BROWNFIELD | HYBRID`, Profile은 `LITE | STANDARD | ENTERPRISE`다.

## 4. Bootstrap

```bash
python sdlc/scripts/bootstrap_project.py \
  . \
  ai-sdlc.yaml \
  sdlc/config/provider-registry.example.yaml \
  -o .ai-sdlc/project-bootstrap.yaml
```

Bootstrap은 Repository 전체를 무제한 Scan하지 않는다. 제한된 marker만 확인하여 AUTO Mode 후보와 Provider 상태, OPEN Decision을 만든다.

- 기존 자산 marker 없음 → GREENFIELD 후보
- Source/Build marker 존재 → BROWNFIELD 후보
- Source Provider 미연결 → Source claim 관련 Action만 Guard
- Greenfield 기술 Stack 미정 → OPEN Decision으로 보존

## 5. Artifact Profile을 실제 Plan으로 변환

```bash
python sdlc/scripts/resolve_artifact_profile.py \
  sdlc/config/artifact-profiles.yaml \
  ai-sdlc.yaml \
  -o .ai-sdlc/artifact-plan.yaml
```

Profile Rule:

- `MUST` → 생성 대상
- `OFF` → 생성하지 않음
- `OPTIONAL / CONDITIONAL / CONDITIONAL_L2_ONLY / CONFIGURABLE_L1_L2` → 기본 비생성, 필요할 때 Stage Pack의 `execution.requested_outputs`로 요청

따라서 LITE를 선택하면 Conditional 문서가 자동으로 모두 생성되지 않는다. 내부 Canonical Trace/Safety는 유지한다.

## 6. Greenfield / Brownfield 첫 Prompt

Bootstrap의 `resolved_mode`를 보고 다음 Prompt를 사용한다.

- Greenfield: `starter/prompts/greenfield-first-prompt.md`
- Brownfield: `starter/prompts/brownfield-first-prompt.md`

Greenfield 기술 선택은 AI가 임의 확정하지 않는다. Brownfield Source Behavior도 Business Truth로 승격하지 않는다.

## 7. Brownfield Source Inventory

Brownfield이면 Requirement 추적 전에 제한된 Inventory를 먼저 만든다.

```bash
python sdlc/scripts/discover_source_inventory.py \
  . \
  <SOURCE_REVISION> \
  -o .ai-sdlc/source-inventory.yaml
```

Inventory는 Program/Business 관계를 확정하지 않는다. Inventory 결과에 따라 `source-analyzers.yaml`의 Java/Spring, SQL/DB, Batch/Scheduler, Interface Adapter를 선택한다. 없는 Analyzer는 OPEN으로 남긴다.

## 8. 첫 Requirement → INTAKE Stage Pack

기존 고객 Requirement ID 또는 입력 ID를 그대로 Source ID로 사용한다. Candidate ID는 Canonical ID가 아니다.

```bash
python sdlc/scripts/create_initial_stage_pack.py \
  .ai-sdlc/project-bootstrap.yaml \
  <SOURCE_REQUIREMENT_ID> \
  <SOURCE_REVISION_OR_NO_SOURCE> \
  -o .ai-sdlc/intake-pack.yaml
```

## 9. Stage Pack → 실행 Plan

```bash
python sdlc/scripts/resolve_stage_execution.py \
  sdlc/config/stage-routing.yaml \
  .ai-sdlc/intake-pack.yaml \
  --artifact-plan .ai-sdlc/artifact-plan.yaml \
  -o .ai-sdlc/stage-execution.yaml
```

Stage Router가 Skill, Required/Optional Capability, Output, Next Stage를 결정한다. Caller/Agent가 Required Capability를 임의로 만들지 않는다.

부작용 Action은 Stage Pack의 `execution.requested_actions`에 명시적으로 들어온 경우에만 Required Capability가 된다.

## 10. Provider Runtime Context 생성

```bash
python sdlc/scripts/build_command_context.py \
  .ai-sdlc/intake-pack.yaml \
  .ai-sdlc/stage-execution.yaml \
  --command /work \
  -o .ai-sdlc/command-context.yaml
```

Source write/Test execution/Canonical publish 같은 Write Action은 `expected_revision`, `idempotency_key`, `permission_proof_ref`가 없으면 Human Action blocker가 생성된다.

그 후 기존 P0 Runtime을 사용한다.

```bash
python sdlc/scripts/execute_command_runtime.py \
  sdlc/config/provider-registry.example.yaml \
  .ai-sdlc/command-context.yaml \
  -o .ai-sdlc/command-result.yaml
```

## 11. Source 변경 후 Reverse Sync

Language/Framework Analyzer는 변경을 `source-change-evidence.yaml` 계약의 signal로 변환한다. Core는 특정 Java/업무 문자열을 해석하지 않는다.

```bash
python sdlc/scripts/build_reverse_sync_from_signals.py \
  <SOURCE_CHANGE_EVIDENCE> \
  <REFERENCE_GRAPH> \
  sdlc/config/reverse-sync-classification.yaml \
  -o .ai-sdlc/reverse-sync-candidate.yaml
```

자동 STALE 전파는 **CONFIRMED Reference Graph의 직접 관계만** 사용한다. RQ/FR/BR/PROC/FTR/AC는 Source 변경으로 자동 overwrite하지 않고 REVIEW_CANDIDATE로 보호한다.

## 12. 역할별 시작점

| 역할 | 먼저 볼 것 | 주 동작 |
|---|---|---|
| PM | `docs/00_관리/전체작업목록.md` | `/check`, 우선순위/담당/일정 관리 |
| BA/분석 | Requirement + Stage Pack | `/work RQ-xxxx` |
| 설계/개발 | Design/PGM/TASK + Stage Pack | `/work TASK-xxxx` |
| 테스트 | AC/TC + Test Execution Evidence | `/work`, `/check` |
| Harness 관리자 | `ai-sdlc.yaml`, Provider/Overlay | Bootstrap/Provider 연결 |

## 13. Safety Invariants

다음은 Profile/Customization과 무관하게 제거하지 않는다.

- Human Truth != Source Evidence
- Candidate != Canonical
- Test Design Coverage != Runtime PASS
- OPEN Preservation
- UNKNOWN_AFTER_WRITE
- Side-effect Guard
- Revision/Hash
- Provider Capability Boundary
- Confirmed Trace Only Reverse Sync

## 14. 검증

Structural Redesign Self-test 정의:

```bash
python sdlc/scripts/test_structural_redesign.py
```

CI 정의: `.github/workflows/structural-redesign-selftest.yml`

CI가 실제 실행되지 않았다면 PASS로 간주하지 않는다.

## 상세 문서

- `guides/01_SDLC_전체가이드.md`
- `guides/02_SKILL_사용가이드.md`
- `guides/03_TEMPLATE_산출물가이드.md`
- `guides/04_HARNESS_커스터마이징가이드.md`
- `design/contracts/p0-p1-structural-redesign-v1.md`
