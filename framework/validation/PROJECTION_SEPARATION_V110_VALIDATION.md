# v1.10 Projection Separation 검증 보고서

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

Base Branch: `SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`

## 1. 검증 목적

Canonical 의미와 Engineering/Customer Projection의 문서 토폴로지를 분리하고, Template/Guide/Project Scaffold/Framework Asset Boundary가 v1.10 현재 설계와 일치하는지 확인한다.

## 2. 현재 구현 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| v1.10이 v1.9 변경을 모두 포함 | PASS | Branch compare behind 0 |
| Engineering 기본 Profile | PASS | `ENGINEERING_SDD_COMPACT` |
| Customer 기본/Full Profile | PASS | `CUSTOMER_STANDARD_3`, `CUSTOMER_WATERFALL_FULL` |
| Engineering/Customer topology 독립 | PASS | projection invariant regression |
| Human-maintained Project Config 단일화 | PASS | `.sdlc/project.yaml`, `project_config.py` |
| Stage Semantic Template 원본 통합 | PASS | `sdlc/templates/semantic/` |
| 구 Stage Template alias/symlink/fallback 제거 | PASS | Template role boundary regression |
| Legacy 3/5/Full을 Formal Projection으로 분리 | PASS | `sdlc/templates/tailoring/standard/`, Legacy Profile |
| Guide SoT 현행화 | PASS | `docs/00_시작/`, Guide consistency regression |
| Project Scaffold가 Framework/Legacy default 자산 제외 | PASS | Project scaffold contract + materialization test |
| Framework Design/Archive governance | PASS_BY_STRUCTURE, current-head CI required | `framework/design/README.md`, `framework/archive/README.md`, governance regression |

## 3. Asset Boundary

### Project-facing

- User Guide: `docs/00_시작/`
- Project Config: `.sdlc/project.yaml`
- Runtime: `sdlc/scripts/`의 Project Runtime + 선택 Extension
- Runtime Contract: `sdlc/design/contracts/`
- Stage Semantic Template: `sdlc/templates/semantic/`
- Projection Profile/Template: 선택된 Engineering/Customer/PM 자산

### Framework-only

- `framework/design/`
- `framework/archive/`
- `framework/management/`
- `framework/pilots/`
- `framework/samples/`
- `framework/validation/`
- `tests/`
- `.github/`

## 4. Compatibility Boundary

Stage Semantic Template 경로에는 alias/symlink가 없다.

별도 기능 영역에는 다음 compatibility debt가 남아 있으며 신규 Project Scaffold의 기본 경로가 아니다.

- `sdlc/validation`: 과거 validation asset 참조 경로
- `sdlc/config/customer-document-profile.example.json`: 과거 Customer config 참조 경로
- `runtime_config_v19.py`: thin compatibility wrapper
- `documents.internal.profile`: migration input only
- `STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`: Legacy/Formal Projection

## 5. 최근 자동 검증 Evidence

Framework governance 정리 직전 Head `06bba47918983ee1f94f3ac9050ea30617d9ee5b`에서 다음 Workflow가 모두 성공했다.

- P0 P1 Production Readiness #322 — SUCCESS
- Worklist sync quality #1237 — SUCCESS
- Docs quality #486 — SUCCESS
- Greenfield Work Executor E2E #332 — SUCCESS
- Public Brownfield Pilot #345 — SUCCESS

전체 unittest는 344 tests를 통과했다.

Framework governance 문서/metadata/test 변경 후의 current-head CI는 `framework/validation/FRAMEWORK_GOVERNANCE_V110.md`와 PR #67의 최신 Workflow 결과를 근거로 확인한다.

## 6. Evidence Boundary

자동 CI는 Repository 구조, Runtime Contract, Template/Guide/Projection/Scaffold 일관성을 검증한다. 다음을 대신하지 않는다.

- External Agent 반복 실행의 empirical semantic equivalence
- 일반 프로젝트 참여자의 first-use usability 관찰
- 실제 고객 프로젝트 production deployment
- Confirmed Business Authority가 포함된 Brownfield reconciliation empirical validation

## 7. 판정

Repository/Runtime/Document 구조 기준 판정은 `PASS_WITH_EVIDENCE_BOUNDARY`를 유지한다. 단, Framework governance refresh 자체의 최종 current-head CI 성공 여부를 확인한 뒤 PR의 최신 Head 기준으로 마감한다.
