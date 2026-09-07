# Projection Hygiene V1.10 검토 및 개선 기록

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/hris-hunel-engineering/v1.10.1`

## 1. 목적

개발자와 고객이 사용하는 Projection 문서가 Canonical/Runtime 내부 구조를 그대로 노출하지 않고, 각 사용자가 실제 업무에 필요한 정보만 문서 목적에 맞게 보여주도록 경계를 강화한다.

이번 변경은 Canonical 의미 모델이나 Tailoring Selector를 없애는 작업이 아니다.

```text
Canonical / Stage / Evidence / Runtime Metadata
        ↓
Audience-specific Projection Selection
        ↓
Visibility Filter / Translation
        ↓
Engineering 또는 Customer Human Document
```

Machine-side에서는 기존 ID와 관계를 계속 유지하고 Human Projection에서만 표현을 정제한다.

## 2. 문제점

변경 전에는 다음 문제가 있었다.

### Engineering Projection

- `RQ/FR/FTR/TASK/PGM/AC/TC` 등 Canonical 분해 구조가 개발자 문서에 직접 노출되었다.
- `OBSERVED/CONFIRMED/OPEN`, `SOURCE_BLOCK/ITERATE/ALERT`, `READY/PARTIAL/EXECUTION_GUARDED` 등 Runtime 상태가 사용자 문서 표현으로 사용되었다.
- HITL Queue에 `Queue ID`, `Recheck At`, `BEFORE_SOURCE_WRITE` 같은 Agent/Runtime 용어가 그대로 보였다.
- Stable Block ID 목록을 사람이 알아야 하는 것처럼 보일 수 있었다.

### Customer Projection

- Customer Template 표면은 자연어 중심이었지만 direct Canonical input이 Entity 전체 Field/Relation을 먼저 펼친 뒤 Renderer Sanitizer로 제거하는 구조였다.
- Canonical 필드가 확장되면 Fuzzy Section Matching과 결합되어 내부 정보가 고객 문서에 유입될 가능성이 있었다.
- `근거_상세_부록`이 일부 기본 Profile에서 활성화되어 내부 근거를 기본 노출할 수 있었다.
- README의 Canonical ID 유지 표현이 Machine-side 추적과 Customer 문서 노출을 혼동시킬 수 있었다.

## 3. 채택한 Visibility 모델

새 기준은 `sdlc/design/contracts/projection-visibility-contract.json`에 명시한다.

### Machine-only 기본값

- Canonical Entity Type / ID / Revision
- Relation Type
- Provenance / Evidence Class / Confidence
- Stage Taxonomy / Change Level
- Runtime Guard / Queue Code
- Queue ID / Block ID
- Hash / Locator
- Projection Lifecycle State

### Engineering-visible

- 기능 목적 / 업무 규칙 / 시나리오 / 범위
- Program / Source / Symbol / Method
- Query / Table / Column
- Interface / Batch / Procedure
- Authorization / Input·Output / Transaction
- 구현 순서 / Test 방법 / 실제 구현 결과
- 개발에 영향을 주는 미확정 사항

### Customer-visible

- 요청 배경 / 기대 결과
- 현재 업무 / 개선 후 업무
- 주요 업무 규칙
- 범위 / 제외 범위
- 업무 영향
- 고객 결정 필요사항 / 합의사항 / 미확정 사항
- 테스트 / 인수 기준과 결과
- 운영 인수

## 4. Engineering Standard 개선

다음 Standard Engineering Template을 정제했다.

- `sdlc/templates/engineering/standard/00_work-map.md`
- `sdlc/templates/engineering/standard/work-unit-sdd.md`
- `sdlc/templates/engineering/standard/program-spec.md`

변경 원칙:

1. Canonical/Runtime 내부 taxonomy를 사람 문서에서 제거하거나 자연어로 번역한다.
2. 실제 개발에 필요한 Program/Source/Query/Table/Transaction 등은 유지한다.
3. Stable Block ID는 `<!-- BLOCK_ID: ... -->` HTML comment로 유지한다.
4. 사람이 Block ID를 외워 입력할 필요는 없다. 절 제목/내용을 자연어로 지정하면 Agent가 Block으로 해석한다.
5. HITL Queue는 `추가 확인이 필요한 사항`으로 표시한다.

예:

```text
SOURCE_BLOCK      → 개발 전 확인 필요
ITERATE           → 진행 가능·추후 보완
ALERT             → 주의사항
BEFORE_SOURCE_WRITE → 개발 시작 전
BEFORE_TEST       → 테스트 전
BEFORE_VERIFY     → 최종 검증 전
```

## 5. HRIS / hunel Custom Projection 개선

다음 Custom Template에도 같은 Visibility 원칙을 적용했다.

- `sdlc/custom/project/templates/hris-hunel/01_업무정의서.md`
- `sdlc/custom/project/templates/hris-hunel/02_작업지시서.md`

업무정의서에서는 Canonical/Stage/Business Truth 상태 표현을 제거하고 업무 목적, 규칙, 권한, 데이터, 영향, 인수 기준과 확인사항 중심으로 정리했다.

작업지시서에서는 Framework 상태 코드를 제거했지만 실제 개발에 필요한 hunel 고유 정보는 유지했다.

- Program ID
- JSP / Java / XML SQLResource
- `hunelCommonDS`, `Sys_appl_abstract`
- ibsheet
- CUDSQLManager
- `chkAuthMenu`, `chkAuthTrans`
- Procedure / PLSQL
- Query / Table / Column
- Parameter Mapping
- Migration / Rollback

즉 기술 상세를 숨기는 것이 아니라 **Harness 내부 제어정보와 구현정보를 분리**한다.

## 6. Customer Projection — Allowlist First

`customer_projection_runtime.py`의 direct Canonical input을 변경했다.

변경 전:

```text
Canonical Entity 전체 Field + Relation
→ Projection Input
→ Section Matching
→ Sanitizer
→ Customer Document
```

변경 후:

```text
Canonical Entity
→ entity.fields 및 Legacy top-level에서 명시적 Customer-safe Field만 선택
→ Relation expansion 금지
→ Customer Contract Section Mapping
→ Sanitizer 2차 방어
→ Customer Document
```

### 허용 예

- `title`
- `summary`
- `original_requirement`
- `desired_outcome`
- `scope`
- `business_rule`
- `as_is` / `to_be`
- `business_impact`
- `acceptance_criteria`
- `open_items`
- `agreed_items`
- `operations` / `handover`

### 기본 차단 예

- `id`, `entity_type`
- `truth_status`, `status`
- `revision`
- `provenance`
- `evidence_class`, `confidence`
- `stage`, `change_level`
- `queue_id`, `block_id`, `guard_code`
- `hash`, `source_hash`, `locator`
- relation target/type

Canonical relation은 Customer direct input에서 더 이상 자동 펼치지 않는다.

## 7. Customer Contract / Profile

`customer-document-contract.json`은 안전한 Canonical semantic field가 어떤 Customer Section으로 들어갈지 명시적으로 매핑한다.

예:

- `original_requirement`, `desired_outcome` → 요청 및 기대 결과
- `business_rule` → 주요 기능과 업무 규칙
- `scope`, `in_scope`, `out_of_scope` → 범위와 제외범위
- `business_impact`, `functional_impact` → 업무 영향
- `acceptance_criteria` → 테스트와 인수기준
- `operations`, `handover` → 운영 인수

`customer-document-profile.json` 기본값은 모든 Active Customer View에서 다음을 OFF한다.

- 기술 상세 부록
- 근거 상세 부록

프로젝트가 고객 제출 요구에 따라 명시적으로 켜는 것은 허용한다.

## 8. Tailoring Selector와의 관계

`ENGINEERING_SDD_COMPACT.yaml` 또는 `CUSTOMER_STANDARD_3.yaml` 안에서 `RQ`, `FR`, `BR`, `PGM`, `AC`, `TC` 등 Canonical Entity Type을 Source Selector로 사용하는 것은 유지한다.

이것은 **Machine-side 입력 선택 계약**이며 Human Projection 노출과 다른 문제다.

```text
Profile Selector: internal Canonical ID 사용 가능
Human Document: audience가 이해해야 할 표현만 노출
```

따라서 Projection Hygiene 때문에 Canonical Schema나 Tailoring Selector를 약화시키지 않는다.

## 9. HITL Queue와 Block Edit

Queue 의미 상태는 기존 `OPEN / DEFERRED` 계약과 연동한다. 다만 Engineering/Customer Projection은 Machine Queue Code를 그대로 노출하지 않는다.

사람 View:

```text
확인 필요사항
현재 확인 내용 / 제안
확인 담당
개발 영향
다시 확인할 시점
상태
```

Machine-side:

```text
Queue ID
Block ID
SOURCE_BLOCK / ITERATE / ALERT
Recheck At
OPEN / DEFERRED
```

Stable Block ID는 HTML comment로 계속 유지한다.

## 10. Project Scaffold

`projection-visibility-contract.json`을 Project Scaffold required file에 추가했다.

따라서 Framework Source에서 Project Scaffold를 생성해도 Template README가 참조하는 Projection Visibility 계약이 함께 배포된다.

## 11. Regression

다음 테스트를 수정/추가했다.

- `tests/test_hitl_block_edit_ux.py`
  - Hidden Block marker 유지
  - Human body에서 Queue/Guard Machine Code 비노출
- `tests/test_hris_hunel_custom_engineering_profile.py`
  - HRIS 업무정의서/작업지시서의 사용자 표현 정제
  - hunel 구현정보 보존
- `tests/test_projection_visibility_hygiene_v110.py`
  - Visibility Contract
  - Standard/HRIS Template machine vocabulary 비노출
  - Customer technical/evidence appendix 기본 OFF
  - nested `entity.fields`의 safe field만 허용
  - Provenance/Relation/Queue/Change Level 차단
  - safe Canonical 값이 실제 Customer Section으로 연결되는지 확인

기존 Customer Projection Pilot에서 프로젝트가 명시적으로 선택한 Optional Appendix는 계속 허용한다.

## 12. 검증 상태

이 문서는 설계 및 정적 회귀 의도를 기록한다.

GitHub Actions 또는 실제 Test Runner 결과가 확인되기 전에는 `PASS`, `VALIDATED`, `Production Ready`의 증거로 사용하지 않는다.
