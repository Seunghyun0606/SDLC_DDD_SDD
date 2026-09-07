# Project 설정 가이드

## 1. 사용자가 관리하는 설정은 하나

프로젝트 참여자가 직접 관리하는 기준 Config는 `.sdlc/project.yaml`이다. Runtime에서 만들어지는 effective config나 legacy snapshot을 직접 편집하지 않는다.

기본 실행:

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
```

`setup`은 Repository에서 확인 가능한 Source root, Build/Test, Language/Framework/DB 후보를 먼저 탐색하고 확인할 수 없는 값은 `unresolved`로 남긴다.

이 문서는 **설정 순서와 운영 방법**을 설명한다. 각 Config Key의 역할, 허용값, 기본값, Runtime 적용 여부, 주의사항을 모두 보려면 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 사용한다.

특히 Config Key는 다음을 구분한다.

```text
Runtime Switch
Resolved Policy
Document / Agent Context
Extension Config
Dead Config
```

지원하지 않는 일반 Key는 조용히 무시하지 않고 Dead Config로 실패시킨다.

## 2. Agent 실행 방식

Project Config에는 특정 Agent 제품명을 고정하지 않는다. 같은 Repository를 Cursor, Codex, Claude Code 등 서로 다른 Host에서 사용할 수 있기 때문이다.

기본값은 `INTERACTIVE`다.

```yaml
agent:
  execution: INTERACTIVE
```

- `INTERACTIVE`: 현재 대화/IDE/CLI 세션의 Agent가 작업한다.
- `HEADLESS`: CI/Batch 등에서 Harness가 설정된 외부 Provider를 실행한다.

두 모드는 Agent 시작 방식만 다르고 Target Graph Guard, Business Truth Guard, Stage Result Validator, Canonical Apply는 같다.

`HEADLESS`를 선택했다면 `agent.provider.command`가 필요하다. 반대로 `INTERACTIVE`에서 `agent.provider.*`를 같이 쓰면 Config 오류다. 상세 옵션은 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 본다.

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

Customer direct Canonical 입력은 Allowlist-first다. Canonical Relation/Revision/Provenance/Confidence 같은 Machine detail을 고객 문서 생성 입력으로 먼저 펼친 뒤 숨기는 방식이 아니라, 고객에게 허용된 의미 필드만 선택하고 Sanitizer를 2차 방어로 사용한다.

## 4. Legacy 설정은 신규 작성에 사용하지 않는다

v1.10 신규 프로젝트에서는 `documents.engineering.profile`만 사용한다.

기존 v1.9 프로젝트에 남아 있는 `documents.internal.profile`은 Runtime이 Migration 호환 입력으로 읽을 수 있지만 신규 `.sdlc/project.yaml`에는 다시 작성하지 않는다.

`STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`은 기존 Formal 문서 체계를 유지해야 할 때 사용하는 Compatibility Profile이며 신규 프로젝트 기본값이 아니다.

## 5. Change Level은 어디서 정의하는가

Change Level의 표준 의미와 실행 깊이는 다음 두 곳이 기준이다.

```text
sdlc/design/contracts/change-level-contract.json
sdlc/config/change-execution-policy.json
```

- Contract: L1~L5의 의미, Override/History/Safety 정책
- Execution Policy: Level별 Semantic Work, Evidence, Review, 기본 내부 진입 Stage

현재 표준 의미:

| Level | 이름 | 대표 의미 | 기본 내부 진입 |
|---|---|---|---|
| L1 | MICRO | 단일 국소 변경 | DEVELOPMENT |
| L2 | LOCAL | 제한된 복수 Component/Rule 영향 | DEVELOPMENT |
| L3 | FEATURE | 기능 단위 변경 | DESIGN |
| L4 | PROCESS | 업무 Process/Cross-domain 영향 | PROCESS |
| L5 | ARCH | Architecture/Security/Migration 고위험 영향 | IMPACT |

중요한 점은 **기본 진입 Stage가 Human 문서 존재 여부를 결정하는 기준이 아니라는 것**이다.

```text
Change Level = 실행 깊이 / Evidence / Review 필요성
Stage        = 내부 Execution Semantic / 재진입 초점
Profile      = Human Artifact topology
```

L1/L2 Fast Path에서도 Source 변경 전 다음 세 의미 검증은 유지한다.

- `Requirement Intent Decomposition` — 요구 의도와 변경 경계를 분해
- `AS-IS Source Analysis` — 현재 Source/Config/Data 흐름 확인
- `Impact Check` — 직접 및 명백한 주변 영향 확인

## 6. AUTO / MANUAL / 최소 Level

### AUTO

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
```

Agent/Runtime이 Canonical 구조와 Typed Evidence로 Level을 판정한다. `minimum_level`을 L2 또는 L3로 두면 AUTO가 그 아래로 내려가지 않는다.

`minimum_level`은 AUTO 판정의 하한이지 모든 명시적 Override의 절대 하한은 아니다. Evidence 기반 실제 안전 하한은 `safety_floor`다.

### 프로젝트 전체 MANUAL

```yaml
change:
  level_policy: MANUAL
  default_level: L3
```

모든 Target의 기본 Level을 사람이 정해야 하는 프로젝트에서 사용한다. Target별 Level과 Human Runtime Override가 있으면 그것들이 우선한다.

## 7. Target별 사전 Level 지정

특정 요구사항만 사전에 Level을 정할 수 있다.

```yaml
change:
  level_policy: AUTO
  minimum_level: L1
  target_levels:
    RQ-001:
      level: L3
      reason: "업무규칙과 기능 영향을 상세 검토해야 하는 요구사항"
    RQ-002:
      level: L4
      reason: "승인 Process와 타 모듈 영향 존재"
```

Target별 지정은 AUTO 관측값보다 우선한다. 사전 정의해 두면 `/work --target RQ-001`부터 L3가 Effective Level이 된다.

Safety Floor보다 낮은 값을 강제하는 것은 일반 설정이 아니다. 꼭 필요한 경우에만 Risk Acceptance를 명시한다.

```yaml
    RQ-003:
      level: L2
      reason: "검토 결과 외부 Interface가 실제 변경 대상이 아님을 확인"
      accept_below_safety_floor: true
```

이 값은 단순 편의를 위해 사용하지 않는다.

## 8. 작업 중 Level 올리기/내리기

사용자는 자연어로 요청할 수 있다.

```text
RQ-001은 L3로 진행해줘. 업무규칙 검토가 필요해서야.
RQ-001을 L4에서 L2로 낮춰줘. 조회조건 한 곳만 영향 있는 것으로 확인됐어.
RQ-001 Level override를 해제하고 AUTO로 다시 판단해줘.
```

Runtime 명령으로는 다음과 같다.

```bash
python sdlc/scripts/change_execution_runtime.py set-level \
  --target RQ-001 --level L3 --reason "업무규칙 검토 필요"

python sdlc/scripts/change_execution_runtime.py show --target RQ-001

python sdlc/scripts/change_execution_runtime.py clear-level \
  --target RQ-001 --reason "AUTO 재평가"
```

자동 판정의 **자동 강등은 금지**한다. 하지만 사람이 근거와 이유를 명시한 downgrade는 허용한다. 현재 Evidence의 `safety_floor`보다 낮추려면 별도 Risk Acceptance가 필요하다.

```bash
python sdlc/scripts/change_execution_runtime.py set-level \
  --target RQ-001 --level L2 \
  --reason "검토 결과 Cross-domain 영향 없음" \
  --accept-below-safety-floor
```

현재 우선순위는 다음처럼 이해한다.

```text
Human Runtime Override
→ project.yaml target_levels
→ MANUAL default_level
→ AUTO classification + minimum_level
```

## 9. Level 이력은 어디에 남는가

Target별 Runtime state에 자동으로 남는다.

```text
sdlc/runtime/change-level/<TARGET>.json
```

주요 필드:

```text
observed_change_level   Evidence 기반 AUTO 관측값
effective_change_level 실제 실행에 적용되는 값
level_source            AUTO / Project Target / Manual / Human Override
safety_floor            현재 Evidence 기준 최소 안전 수준
classification_reason   판정/결정 이유
level_history           최초 판정, 승격, 명시적 강등, Override 해제 이력
human_override          현재 Human Override가 있으면 그 내용
```

따라서 상세 문서가 짧은 L1 작업도 **왜 L1이었는지와 이후 L3로 올렸는지**를 Runtime 이력에서 확인할 수 있다.

## 10. Level 변경 후 문서를 다시 만드는 방법

Level을 바꾼 뒤에는 같은 Target으로 `/work`를 다시 실행한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

새 `/work`는:

1. 새 Effective Level을 읽고
2. `required_semantic_work / evidence / review`를 재계산하고
3. Tailoring Profile을 다시 Resolve하고
4. `required_engineering_artifacts / projection_update_set`을 갱신 대상으로 제시한다.

Agent는 부족한 분석을 보완한 뒤 해당 Projection들을 Canonical/Evidence 기준으로 다시 만든다.

## 11. Change Level과 문서 Profile을 섞지 않는다

Profile이 문서 topology를 고정해야 하는 경우 `projection_topology: PROFILE_PRIMARY_SET`을 사용할 수 있다.

예: HRIS Custom 2종

```text
CUSTOM_HRIS_HUNEL_ENGINEERING
├─ 01_업무정의서.md
└─ 02_작업지시서.md
```

이 Profile은 L1~L5와 무관하게 2종을 유지한다.

```text
L1/L2 → 두 문서 모두 유지, 필요한 내용만 CONCISE
L3/L4 → 두 문서 모두 유지, STANDARD
L5    → 두 문서 모두 유지, FULL
```

L1/DEVELOPMENT이면 `02_작업지시서`가 주 편집 문서일 수 있지만 `01_업무정의서`도 짧게 갱신한다. 예를 들어 실제 근거가 그렇다면 `업무 정책 변경 없음`, `국소 조회조건 수정`, `주변 영향 없음` 정도로 기록한다. 상세 Process를 억지로 만들어내지는 않는다.

즉 **분석 깊이를 줄이는 것과 Profile-required 문서를 없애는 것은 다른 문제다.** Profile의 topology를 유지할지 Stage-match로 조건부 생성할지는 Profile이 결정한다.

## 12. Customer Scope

```yaml
documents:
  customer:
    scope: RQ  # RQ | MILESTONE | PROJECT
```

- `RQ`: 요구사항 단위 협의
- `MILESTONE`: Release/Milestone 수준으로 운영하려는 정책
- `PROJECT`: 프로젝트 최종 수준으로 운영하려는 정책

주의: 현재 low-level Customer Projection Runtime은 `--target`을 받는 Target 단위 생성기다. `scope: MILESTONE` 또는 `PROJECT`만 적는다고 여러 RQ가 자동 병합되는 것은 아니다. 실제 집계는 선택 Profile이나 상위 Orchestration이 구현해야 한다.

## 13. 직접 수정 정책

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

`manual_edit_policy`는 Lifecycle 정책이지 OS File Permission이 아니다. `HUMAN_REVIEW`를 사용해도 의미 변경은 Canonical Round-trip이 필요하다.

## 14. Custom Profile 위치

```text
sdlc/custom/project/
├─ tailoring/
└─ templates/
   ├─ engineering/
   └─ customer/
```

Framework 표준을 고객 프로젝트에서 직접 고치지 않는다.

실제 artifact output path의 권위는 선택한 Profile의 `output_path`다. `documents.*.output_root`만 바꿔 Profile 경로가 자동 치환된다고 가정하지 않는다.

## 15. 사람이 직접 관리하지 않는 파일

다음은 Runtime이 생성한다.

```text
.sdlc/runtime/effective/project-profile.json
.sdlc/runtime/effective/source-profile.json
.sdlc/runtime/effective/agent-execution.json
.sdlc/runtime/effective/agent-provider.json
.sdlc/runtime/effective/project-context.json
.sdlc/runtime/effective/config-usage.json
.sdlc/runtime/effective/tailoring-config.json
sdlc/runtime/change-level/<TARGET>.json
```

Target Change Level Runtime state도 이력 확인용이지 사용자가 JSON을 직접 수정하는 파일이 아니다. 변경은 Project Config 또는 `set-level/clear-level` 경계로 수행한다.

## 16. 설정 검증

```bash
python sdlc/scripts/harness.py check --setup
```

설정이 실제로 어느 범주로 소비되는지 확인하려면 다음을 본다.

```text
.sdlc/runtime/effective/config-usage.json
```

`dead`에 Key가 남아 있으면 설정이 적용된 것으로 간주하지 않는다.

Framework 관리자가 Profile을 검증할 때:

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile ENGINEERING_SDD_COMPACT
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOMER_STANDARD_3
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOM_HRIS_HUNEL_ENGINEERING
```

`INTERACTIVE_HANDOFF_READY`나 `PLAN_READY`는 완료가 아니다. Artifact와 Stage Result를 만든 뒤 동일한 Validator/Target Graph/Business Truth/Canonical Guard를 통과해야 완료다.

## 17. 옵션별 상세 Reference

다음 항목을 개별적으로 확인해야 하면 `02A_PROJECT_CONFIG_옵션_상세가이드.md`를 사용한다.

- `schema_version`
- `project.*`
- `delivery.profile`
- `change.*` 전체와 Level 우선순위
- `agent.execution / agent.provider.*`
- `technology.build / test`
- `source.roots / test_roots / resource_roots / excludes`
- `git.*`
- `architecture.* / coding.* / data.* / interface.* / security.* / deployment.*`
- `documents.engineering/customer/pm/machine.*`
- `documents.customer.projection_contract / projection_config`
- `unresolved`
- `extensions.*`
- Runtime / Document Context / Dead Config 분류
