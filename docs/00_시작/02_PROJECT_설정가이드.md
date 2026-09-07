# Project 설정 가이드

## 1. 사용자가 관리하는 설정은 하나

프로젝트 참여자가 직접 관리하는 기준 Config는 `.sdlc/project.yaml`이다. Runtime에서 만들어지는 effective config나 legacy snapshot을 직접 편집하지 않는다.

## 2. 문서 Projection 설정

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

Engineering Profile과 Customer Profile은 독립이다. 다음 조합이 모두 정상이다.

```text
Engineering 2 / Customer 3
Engineering 3 / Customer 5
Engineering 5 / Customer 3
Custom Engineering N / Custom Customer M
```

## 3. Legacy `documents.internal.profile`

Migration 기간 동안 다음은 계속 읽는다.

```yaml
documents:
  internal:
    profile: STANDARD_5
```

Resolution 우선순위:

```text
documents.engineering.profile
→ 없으면 documents.internal.profile
→ 둘 다 없으면 ENGINEERING_SDD_COMPACT
```

`internal`은 호환 alias이며 신규 프로젝트의 개념 모델은 `engineering`을 사용한다.

`STANDARD_5`와 `STAGE_ORIENTED_FULL`은 기존 고객/계약/단계 지향 문서 구조를 유지해야 할 때 쓰는 Legacy/Formal 호환 Profile이다. 신규 프로젝트 기본값은 아니다.

## 4. Change Level과 문서 Profile을 섞지 않는다

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

## 5. Customer Scope

```yaml
documents:
  customer:
    scope: RQ  # RQ | MILESTONE | PROJECT
```

- `RQ`: 요구사항 단위 협의
- `MILESTONE`: Release/Milestone 제출
- `PROJECT`: 최종 프로젝트 제출

Profile이 여러 RQ를 하나의 고객 문서로 합칠 수 있지만 새로운 Reporting Engine을 따로 만들지 않는다.

## 6. 직접 수정 정책

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

## 7. Custom Profile 위치

프로젝트별 Custom은 한 곳을 우선 사용한다.

```text
sdlc/custom/project/
├─ tailoring/
└─ templates/
   ├─ engineering/
   └─ customer/
```

Framework 표준(`sdlc/tailoring/standard`, `sdlc/templates/...`)을 고객 프로젝트에서 직접 고치지 않는다.

## 8. 설정 검증

일반 사용자는 다음만 사용한다.

```bash
python sdlc/scripts/harness.py check --setup
```

Framework 관리자가 Profile을 검증할 때:

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile ENGINEERING_SDD_COMPACT
python sdlc/scripts/tailoring_runtime.py validate-profile --profile CUSTOMER_STANDARD_3
```
