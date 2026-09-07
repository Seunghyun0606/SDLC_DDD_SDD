# SDLC Harness 시작하기 — v1.10 Projection Separation

## 1. 3가지만 먼저 이해한다

- **Canonical Spec**: 프로젝트 의미와 관계의 원장(Source of Truth)
- **Engineering Document**: 개발자/Agent가 구현하기 위해 보는 Living Spec
- **Customer Document**: 고객과 협의·제출·인수하기 위한 Human-oriented View

Engineering과 Customer는 같은 Canonical을 보지만 **문서 수, 순번, Template, Lifecycle이 서로 독립**이다.

```mermaid
flowchart LR
  R[Requirement / Change] --> C[Canonical Spec]
  C --> E[Engineering Projection\nWork Map / SDD]
  C --> U[Customer Projection\nWaterfall Deliverables]
  E --> S[Source] --> T[Test / Verify]
  S --> C
  T --> C
  C --> U
```

## 2. 일반 사용자가 하는 일

```bash
python sdlc/scripts/harness.py setup --name <project> --mode <AUTO|GREENFIELD|BROWNFIELD|HYBRID>
python sdlc/scripts/harness.py intake <requirements.xlsx>
python sdlc/scripts/harness.py work --target RQ-001
python sdlc/scripts/harness.py check RQ-001
```

설계/Evidence/Program Mapping을 보완할 때는 `/work` 흐름을 사용한다. 요구사항, Business Rule, Scope, TO-BE Behavior가 바뀌면 `/change` 흐름을 사용한다.

일반 사용자는 내부 Stage 전체 taxonomy, Canonical JSON Schema, Runtime Python 호출 관계를 배울 필요가 없다.

## 3. 신규 Project Config 기본값

`.sdlc/project.yaml`이 Human-maintained 설정의 기준이다.

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

Migration 기간에는 `documents.internal.profile`도 읽는다. 우선순위는 다음과 같다.

1. `documents.engineering.profile`
2. 없으면 `documents.internal.profile`
3. 둘 다 없으면 `ENGINEERING_SDD_COMPACT`

`STANDARD_5`와 `STAGE_ORIENTED_FULL`은 Legacy/Formal 호환용이다.

## 4. Engineering 기본 문서

`ENGINEERING_SDD_COMPACT`의 기본 구조는 다음과 같다.

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<TARGET>.md
└─ programs/<TARGET>.md   # 필요할 때만
```

- `00_work-map.md`: RQ → Work → TASK → PGM → Source → AC/TC 연결판
- `specs/...`: 기능/업무 단위 Living SDD
- `programs/...`: 실제 Source 구현 Delta가 별도로 필요한 경우만 생성

Engineering 문서는 `semantic_owner: CANONICAL`, `projection_owner: AGENT`, 기본 `manual_edit_policy: TYPO_ONLY`다. 오탈자 외 직접 수정은 Canonical을 자동 변경하지 않으며 Projection 상태에서 경고 대상으로 취급한다.

## 5. Customer 기본 문서

기본 `CUSTOMER_STANDARD_3`:

- A01 요구·업무·기능 합의서
- A02 영향·개발범위 공유서
- A03 테스트·인수·운영 결과서

필요하면 `CUSTOMER_WATERFALL_FULL` 8종을 선택할 수 있고, 프로젝트 Custom Profile로 1/3/5/8/13/N종을 정의할 수 있다.

Customer Runtime은 Engineering Profile ID, Engineering 문서 수/순번, expected path를 사용하지 않는다. Customer Profile + Canonical/semantic metadata/Evidence를 사용한다.

## 6. `/work`와 `/change` 경계

### `/work`

Canonical Business 의미는 유지하면서 다음을 보완한다.

- AS-IS Source Evidence
- 상세 설계
- Program/Source Mapping
- Development Task
- AS-BUILT
- Test/Verification

### `/change`

Canonical 의미가 바뀌는 경우다.

- Requirement 변경
- Business Rule 변경
- TO-BE Behavior 변경
- Scope/정책 변경

`/change` 후 영향 Engineering/Customer Projection은 `STALE_VIEW`가 되고 재생성/재검수가 필요하다.

## 7. Customer Final Review

Customer 문서는 진행 중 `PENDING_REVIEW → CURRENT`로 관리할 수 있다. 최종 제출 직전에는 `FINAL_REVIEW`에서 사람이 문구/표현을 수정할 수 있다.

Final Review 이후 Canonical이 바뀌면 자동 overwrite하지 않는다.

```text
FINAL_REVIEW + Canonical Change
→ STALE_VIEW
→ Human Edit 존재 표시
→ Regenerate / Re-review 필요
```

업무 정책 자체를 바꾼 Human Edit은 `/change`로 되돌린다.

## 8. Change Level / Stage / Document는 다르다

- Change Level = 실행 깊이 / Evidence / Review 필요성
- Stage = 내부 Execution Semantic
- Projection Profile = 사람에게 어떤 Artifact를 보여줄지

따라서 `Stage = Document`, `Change Level = Document Count`로 해석하지 않는다.

## 9. 다른 프로젝트에 적용할 때

Repository 전체를 복사하지 않는다. Framework의 기존 Project Scaffold 선택기가 필요한 Runtime/Profile/Template/User Guide만 배포한다.

```bash
python sdlc/scripts/build_project_scaffold.py --root . --output <outside-target-directory>
```

Framework Test/Pilot/관리문서/Design History는 Project Runtime에서 제외한다.

## 10. 다음 문서

- 프로젝트 설정: `02_PROJECT_설정가이드.md`
- Profile/Customizing: `03_TAILORING_설정가이드.md`
- Engineering/Customer Template: `04_TEMPLATE_및_산출물_가이드.md`
- 이해관계자별 사용: `05_이해관계자별_작업가이드.md`
- 다른 Repository 적용: `06_CUSTOM_SCAFFOLD_적용가이드.md`
