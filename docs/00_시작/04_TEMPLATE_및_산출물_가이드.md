# Template 및 산출물 가이드

## 1. 문서는 두 종류로 생각한다

### Engineering Projection

개발자와 Agent가 실제 구현을 수행하기 위한 Living Spec이다.

기본 위치:

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<WORK-UNIT>.md
└─ programs/<PGM>.md   # 필요할 때만
```

### Customer Projection

고객과 협의·제출·검수·인수하기 위한 Human-oriented Waterfall View다.

기본 위치:

```text
docs/20_고객/<TARGET>/
├─ A01_요구_업무_기능_합의서.md
├─ A02_영향_개발범위_공유서.md
└─ A03_테스트_인수_운영_결과서.md
```

Profile에 따라 `docs/20_customer/...` 같은 Custom output root를 사용할 수 있다.

## 2. Work Map

목적은 상세설계를 반복하는 것이 아니라 다음 질문에 빨리 답하는 것이다.

- 무엇을 구현해야 하는가?
- 어떤 기능/업무 단위인가?
- 어떤 Program/Source를 수정하는가?
- 어떤 Test로 확인하는가?
- 현재 어디까지 진행됐는가?

최소 연결:

```text
RQ → FR/FTR → WP → Design TASK / Development TASK / Test TASK
   → PGM → ART/Source → AC → TC
```

## 3. Work Unit SDD

Stage 문서를 이어 붙인 문서가 아니다. 하나의 기능/업무 단위가 Lifecycle을 따라 발전한다.

```text
CHANGE → IMPACT → SPEC → PLAN → IMPLEMENT → VERIFY → AS-BUILT
```

표준 Section:

1. 목적 / Functional Intent
2. AS-IS Evidence
3. TO-BE Spec
4. Business Rule / Decision
5. 영향 범위
6. 구현 Mapping
7. Program / Data / Interface 영향
8. Development Task
9. AC / Test
10. Open / Risk / Guard
11. AS-BUILT
12. Verification

## 4. Program Spec

Program Spec은 Functional 의미를 다시 쓰는 문서가 아니다.

```text
Functional/Work Unit Spec = 무엇을 왜 어떻게 동작시킬 것인가
Program Spec              = 실제 어떤 Source에 어떤 Delta를 구현할 것인가
```

Source에서 다시 생성 가능한 Query/Table/Symbol/Locator/Hash는 Machine-derived Evidence로 관리한다.

## 5. Engineering 직접 편집

Engineering Template 상단에는 다음 원칙이 표시된다.

```text
오탈자 → 직접 수정
설계/Evidence/Program Mapping → /work
Requirement/Business Rule/TO-BE → /change
```

Generated hash와 파일이 다르면 Projection Lifecycle에서 `MANUAL_EDIT_DETECTED` 경고가 가능하며, 그 사실만으로 Canonical을 자동 변경하지 않는다.

## 6. Customer Template

기본 3종은 다음 목적에 맞춘다.

- A01: 요구/업무/기능 합의
- A02: 영향/개발범위 공유
- A03: 테스트/인수/운영 결과

`CUSTOMER_WATERFALL_FULL`은 같은 semantic contract를 8개의 제출 단위로 split한 예시다. 프로젝트는 Custom Profile로 다른 N종을 만들 수 있다.

## 7. Customer Final Human Edit

진행 중 문서는 Agent-generated View다. Final Submission 직전 `FINAL_REVIEW`에서 표현/레이아웃을 사람이 다듬을 수 있다.

- 표현 수정 → Canonical 변화 없음
- Business Rule 수정 → `/change`
- Final Review 이후 Canonical 변경 → `STALE_VIEW`, 자동 overwrite 금지, 재검수 필요

Rich Text Merge Engine을 따로 만들지 않는다.

## 8. Template을 추가할 때 체크

Engineering Template:

- Functional 의미를 중복하지 않는가?
- TASK/PGM/Source/AC/TC가 연결되는가?
- AS-BUILT/Verification을 담을 수 있는가?
- 직접 편집 정책이 보이는가?

Customer Template:

- 고객에게 필요한 자연어 문맥인가?
- 내부 ID/Hash/Confidence가 불필요하게 노출되지 않는가?
- 어떤 `projection_type`의 의미를 표현하는가?
- Engineering 파일명/순번에 의존하지 않는가?

## 9. Framework Standard / Project Custom / Generated 구분

```text
Framework Standard
- sdlc/tailoring/standard/
- sdlc/templates/

Project Custom
- sdlc/custom/project/

Generated
- sdlc/runtime/
- docs/10_engineering/
- docs/20_고객/ 또는 Customer Profile output root
```

고객별 요구 때문에 Framework Standard 자체를 직접 수정하지 않는다.
