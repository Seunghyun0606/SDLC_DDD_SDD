# v1.10 Framework Design / Archive Governance 검증

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

## 1. 점검 배경

Runtime/Template/Guide는 v1.10으로 현행화되었지만 Framework 내부 설계 metadata가 같은 수준으로 갱신되었는지 별도 점검했다.

점검 전 확인된 Gap:

1. `framework/design/branch-version.yaml`이 v1.9 branch/candidate/291 tests를 active metadata로 기록
2. `framework/design/CHANGELOG.md`가 v1.5.1 이후 변경을 기록하지 않음
3. `framework/design/session/SDLC_DESIGN_SESSION_FIRST.yaml`의 current lineage와 branch metadata 경로가 과거 상태
4. `framework/design/`에 current design entrypoint/역할 설명이 없어 역사 Candidate와 현재 SoT 구분이 어려움
5. `framework/archive/`에 v1.9 inventory 하나만 있고 Archive policy/index가 없음
6. `framework/README.md`, `ASSET_INVENTORY_V110.md`, Projection Validation 일부가 최신 Design/Archive 상태보다 뒤처짐

## 2. 조치

### Design

- `framework/design/README.md` 추가
- `framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md` 추가
- `framework/design/branch-version.yaml`을 v1.10 active metadata로 교체
- `framework/design/CHANGELOG.md`에 v1.9/v1.10 변화 추가
- Session metadata의 branch metadata 경로/current lineage/current version을 v1.10으로 갱신

### Archive

- `framework/archive/README.md` 추가
- `framework/archive/INDEX.md` 추가
- 기존 v1.9 active branch metadata를 `framework/archive/design-metadata/branch-version-v1.9.0.yaml`로 원본 보존
- Archive를 superseded active metadata/inventory/migration snapshot 보관소로 정의

### Framework top-level

- `framework/README.md`의 실제 구조/Design-Archive 경계를 현행화
- `framework/ASSET_INVENTORY_V110.md`의 current/history/archive 분류와 Template/Guide 상태 현행화
- `framework/validation/PROJECTION_SEPARATION_V110_VALIDATION.md`의 오래된 검증 Head/Stage Template alias 설명 교정

## 3. Governance 규칙

현재 설계 우선순위:

1. `framework/design/branch-version.yaml`
2. `framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md`
3. `framework/design/CHANGELOG.md`
4. `framework/ASSET_INVENTORY_V110.md`
5. `framework/validation/*V110*.md`
6. 실제 Runtime Contract는 `sdlc/design/contracts/`

과거 `baselines/`, `candidates/`, `reviews/`, `validations/`는 설계 진화 이력이며 현재 Runtime SoT가 아니다.

Archive는 current SoT가 아니며 `INDEX.md`에 대체 경로가 반드시 있어야 한다.

## 4. 자동 회귀

`tests/test_framework_governance_v110.py`에서 최소 다음을 검증한다.

- active branch metadata가 v1.10 Branch를 가리키는지
- active design summary가 존재하는지
- Session metadata가 current branch와 새 metadata 경로를 가리키는지
- Archive README/INDEX/v1.9 metadata snapshot이 존재하는지
- Asset Inventory가 Design/Archive 현재 구조를 설명하는지
- Framework active docs가 구 Stage Template 경로를 다시 사용하지 않는지
- 과거 candidate가 current design SoT로 취급되지 않도록 governance marker가 있는지

## 5. CI Evidence

Framework governance 정리 직전 Head `06bba47918983ee1f94f3ac9050ea30617d9ee5b`의 5개 Workflow는 모두 SUCCESS이며 전체 unittest는 344 tests PASS였다.

본 governance 변경이 포함된 current-head CI 결과는 이 문서의 후속 Evidence section과 PR #67에서 최종 확인한다.

## 6. 판정 경계

이 검증은 Framework repository governance와 자동 회귀 범위다. 실제 외부 Agent/Human/Production 실증을 의미하지 않는다.

현재 구조 판정: `FRAMEWORK_GOVERNANCE_REMEDIATED_PENDING_CURRENT_HEAD_CI`
