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
- 기존 v1.6/v1.9 회귀가 요구하는 validation boundary marker는 `inherited_validation_boundary`에 보존하고, top-level active status는 `ACTIVE_CANONICAL_SOURCE`로 분리

### Archive

- `framework/archive/README.md` 추가
- `framework/archive/INDEX.md` 추가
- 기존 v1.9 active branch metadata를 `framework/archive/design-metadata/branch-version-v1.9.0.yaml`로 보존
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

`tests/test_framework_governance_v110.py`에서 다음을 검증한다.

- active branch metadata가 v1.10 Branch를 가리키는지
- active design summary가 존재하는지
- Session metadata가 current branch와 새 metadata 경로를 가리키는지
- Archive README/INDEX/v1.9 metadata snapshot이 존재하는지
- Asset Inventory가 Design/Archive 현재 구조를 설명하는지
- Framework active docs가 구 Stage Template 경로를 다시 사용하지 않는지
- Changelog가 v1.9와 v1.10 설계 변화를 기록하는지

기존 회귀와 함께 전체 unittest에서 검증되므로 Framework governance가 과거 Validation Boundary 계약을 깨뜨리는 경우에도 실패한다.

## 5. CI Evidence

Framework governance 보정이 반영된 Head `93ee8b6574538f10e8b4a7f03a2957211a5c355c`에서 다음 PR Workflow가 모두 성공했다.

- P0 P1 Production Readiness #325 — SUCCESS
- Worklist sync quality #1243 — SUCCESS
- Docs quality #489 — SUCCESS
- Greenfield Work Executor E2E #335 — SUCCESS
- Public Brownfield Pilot #348 — SUCCESS

`Worklist sync quality`의 full unittest discovery는 **351 tests PASS**이며, 신규 Framework Governance 7개 테스트와 기존 v1.6/v1.9/v1.10 회귀를 함께 포함한다.

이 보고서 파일 자체가 추가된 최종 Branch Head에서도 동일 Workflow를 다시 실행해 PR #67의 current-head evidence로 확인한다.

## 6. 판정 경계

이 검증은 Framework repository governance와 자동 회귀 범위다. 실제 외부 Agent/Human/Production 실증을 의미하지 않는다.

다음은 별도 Evidence가 필요하다.

- External Agent 반복 실행의 의미 동등성
- 일반 프로젝트 참여자의 first-use usability
- 실제 고객 프로젝트 production deployment
- Confirmed Business Authority가 포함된 Brownfield reconciliation empirical validation

## 7. 판정

**FRAMEWORK_GOVERNANCE_PASS_WITH_AUTOMATED_REGRESSION**

현재 `framework/`는 v1.10 Project/Runtime 변경과 연결된 Framework 문서, active design metadata, current design summary, asset inventory, validation report를 갖는다. `framework/design`은 current design과 historical design evolution을 구분하고, `framework/archive`는 superseded active metadata/inventory snapshot만 보존하도록 역할이 분리되었다.
