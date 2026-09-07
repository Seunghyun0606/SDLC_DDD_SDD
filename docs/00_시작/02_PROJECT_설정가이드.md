# Project 설정 가이드

## 1. 사용자가 관리하는 설정은 하나

프로젝트 참여자가 직접 관리하는 기준 Config는 `.sdlc/project.yaml`이다. Runtime에서 만들어지는 effective config나 legacy snapshot을 직접 편집하지 않는다.

기본 실행:

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
```

`setup`은 Repository에서 확인 가능한 Source root, Build/Test, Language/Framework/DB 후보를 먼저 탐색하고 확인할 수 없는 값은 `unresolved`로 남긴다.

## 2. Agent 실행 방식

Project Config에는 특정 Agent 제품명을 고정하지 않는다. 같은 Repository를 Cursor, Codex, Claude Code 등 서로 다른 Host에서 사용할 수 있기 때문이다.

기본값은 `INTERACTIVE`다.

```yaml
agent:
  execution: INTERACTIVE
```

의미:

- 현재 대화/IDE/CLI 세션의 Agent가 Stage Agent다.
- Harness가 별도 LLM subprocess를 다시 실행하지 않는다.
- `/work`는 Work Context와 finalize 경계를 준비한다.
- Agent가 Artifact와 `stage-result.json`을 작성한 뒤 Validator/Canonical Guard를 통과해야 완료다.

CI/Batch처럼 Harness가 외부 Agent를 직접 호출해야 할 때만 `HEADLESS`를 사용한다.

```yaml
agent:
  execution: HEADLESS
  provider:
    id: PROJECT_AGENT_PROVIDER
    timeout_seconds: 180
    command:
      - python
      - path/to/provider_adapter.py
      - --context
      - "{context_path}"
      - --result
      - "{result_path}"
```

`HEADLESS`인데 provider command가 없으면 Config 오류다. 기존 `sdlc/config/agent-provider.json`과 `--provider-command`는 Legacy compatibility 경로다.

## 3. 문서 Projection 설정

권장 기본값:

```yaml
documents:
  engineering:
    profile: ENGINEERING_SDD_COMPACT
    manual_edit_policy: TYPO_ONLY
    freshness: CANONICAL_REVISION

  customer:
    profile: CUSTOMER_STANDARD_3
    scope: RQ
    freshness: CANONICAL_AND_AS_BUILT
    final_review:
      human_editable: true

  pm:
    profile: PM_STANDARD

  machine:
    visibility: HIDDEN
```

### Engineering

개발/설계/Agent가 구현을 수행하기 위한 Living Spec이다. 신규 기본값은 `ENGINEERING_SDD_COMPACT`다.

### Customer

협의/합의/검수/제출/인수용 문서다. 기본은 `CUSTOMER_STANDARD_3`, Full Waterfall이 필요하면 `CUSTOMER_WATERFALL_FULL`을 선택한다.

Engineering Profile과 Customer Profile은 독립이다.

```text
Engineering 2 / Customer 3
Engineering 3 / Customer 5
Engineering 5 / Customer 3
Custom Engineering N / Custom Customer M
```

## 4. Legacy 설정은 신규 작성에 사용하지 않는다

v1.10 신규 프로젝트에서는 `documents.engineering.profile`만 사용한다.

기존 v1.9 프로젝트에 남아 있는 `documents.internal.profile`은 Runtime이 Migration 호환 입력으로 읽을 수 있지만, 신규 `.sdlc/project.yaml` 예제나 프로젝트 Custom Config에는 다시 작성하지 않는다.

Runtime 호환 Resolution은 기존 프로젝트를 깨뜨리지 않기 위한 내부 동작이며, 사용자 개념 모델과 문서 용어는 `engineering`으로 통일한다.

`STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`은 기존 Formal 문서 체계를 유지해야 할 때 사용하는 Legacy compatibility Profile이며 신규 프로젝트 기본값이 아니다.

## 5. Change Level과 문서 Profile을 섞지 않는다

```text
Change Level = 실행 깊이 / Evidence / Review 필요성
Stage        = 내부 Execution Semantic
Profile      = Human Artifact topology
```

Change Level만 보고 Customer 문서 수를 결정하지 않는다. 문서 수는 Project Config의 Profile이 결정한다.

L1/L2처럼 문서가 적은 Fast Path에서도 실제 Source 변경 전 다음 의미 검증은 생략하지 않는다.

- Requirement Intent Decomposition
- AS-IS Source Analysis
- Impact Check

즉, 문서 수를 줄이는 것과 분석을 줄이는 것은 다른 문제다.

## 6. Customer Scope

```yaml
documents:
  customer:
    scope: RQ  # RQ | MILESTONE | PROJECT
```

- `RQ`: 요구사항 단위 협의
- `MILESTONE`: Release/Milestone 제출
- `PROJECT`: 최종 프로젝트 제출

Profile이 여러 RQ를 하나의 고객 문서로 합칠 수 있지만 새로운 Reporting Engine을 따로 만들지 않는다.

## 7. 직접 수정 정책

Engineering:

```text
오탈자 → 직접 수정 가능
설계/Evidence/Source Mapping 보완 → /work
Requirement/Business Rule/TO-BE 변경 → /change
```

Customer:

```text
진행 중 → Generated View
최종 제출 전 → FINAL_REVIEW에서 표현/레이아웃 수정 가능
Business Rule 변경 → /change
```

Projection 직접 수정은 Canonical을 자동 변경하지 않는다.

## 8. Custom Profile 위치

프로젝트별 Custom은 한 곳을 우선 사용한다.

```text
sdlc/custom/project/
├─ tailoring/
└─ templates/
   ├─ engineering/
   └─ customer/
```

Framework 표준(`sdlc/tailoring/standard`, `sdlc/templates/...`)을 고객 프로젝트에서 직접 고치지 않는다.

자세한 Custom Profile/Template 규칙은 `03_TAILORING_설정가이드.md`, `04_TEMPLATE_및_산출물_가이드.md`를 따른다.

## 9. 사람이 직접 관리하지 않는 파일

다음은 Runtime이 생성하거나 Legacy 호환을 위해 유지하는 Machine artifact다.

```text
.sdlc/runtime/effective/project-profile.json
.sdlc/runtime/effective/source-profile.json
.sdlc/runtime/effective/agent-execution.json
.sdlc/runtime/effective/agent-provider.json
.sdlc/runtime/effective/project-context.json
.sdlc/runtime/effective/config-usage.json
```

새 프로젝트에서 위 파일을 여러 개 나눠 수정해 설정을 바꾸지 않는다.

## 10. 설정 검증

일반 사용자는 다음만 사용한다.

```bash
python sdlc/scripts/harness.py check --setup
```

Framework 관리자가 Profile을 검증할 때만 직접 Tailoring validator를 사용한다.

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile ENGINEERING_SDD_COMPACT
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOMER_STANDARD_3
```

`INTERACTIVE_HANDOFF_READY`나 `PLAN_READY`는 완료가 아니다. Artifact와 Stage Result를 만든 뒤 동일한 Validator/Target Graph/Business Truth/Canonical Guard를 통과해야 완료다.
