# v1.10 Projection Separation 검증 보고서

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

Base Branch: `SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`

## 1. 검증 목적

Canonical 의미와 Engineering/Customer Projection의 문서 토폴로지를 분리하고, Template/Guide/Project Scaffold/Framework Asset Boundary가 v1.10 현재 설계와 일치하는지 확인한다.

## 2. 현재 구현 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| v1.10이 v1.9 변경을 모두 포함 | PASS | Branch compare behind 0 |
| Engineering 기본 Profile | PASS | `ENGINEERING_SDD_COMPACT`, direct Tailoring fallback regression |
| Customer 기본/Full Profile | PASS | `CUSTOMER_STANDARD_3`, `CUSTOMER_WATERFALL_FULL` |
| Engineering/Customer topology 독립 | PASS | projection invariant regression |
| Human-maintained Project Config 단일화 | PASS | `.sdlc/project.yaml`, `project_config.py` |
| Stage Semantic Template 원본 통합 | PASS | `sdlc/templates/semantic/` |
| 구 Stage Template alias/symlink/fallback 제거 | PASS | Template role boundary regression |
| Legacy 3/5/Full을 Formal Projection으로 분리 | PASS | `sdlc/templates/tailoring/standard/`, Legacy Profile |
| Guide SoT 현행화 | PASS | `docs/00_시작/`, Guide consistency regression |
| Project Scaffold가 Framework/Legacy default 자산 제외 | PASS | Project scaffold contract + materialization test |
| Bundled Optional / Separate Optional 경계 | PASS | scaffold contract schema 7 + latest review regression |
| Framework Design/Archive governance | PASS | governance regression + latest commit review |

## 3. Asset Boundary

### Project-facing

- User Guide: `docs/00_시작/`
- Project Config: `.sdlc/project.yaml`
- Runtime: `sdlc/scripts/`의 Project Runtime
- Bundled Optional: Standard Scaffold에 동봉되나 선택 시에만 사용하는 command/Profile support
- Separate Optional: Brownfield reverse, Document ingest, External tool 등 별도 Extension
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

## 5. 최신 자동 검증 Evidence

정확한 최신 Review와 구현 보정 검증 Evidence는 다음 문서를 기준으로 한다.

- `framework/validation/LATEST_COMMIT_REVIEW_V110.md`
- PR #67 current-head Workflow 상태

최근 통합 Review에서 검증한 구현 보정 subject head는 `2cf2e2087472996851d997edebe5646899259e18`이며, 해당 Commit에서 5개 PR Workflow가 모두 SUCCESS이고 Full unittest discovery는 **356 tests PASS**였다.

이 보고서와 다른 Evidence 문서가 추가되는 후속 Commit은 자기 자신의 SHA를 문서 안에서 current-head로 고정하지 않는다. 최종 current-head 성공 여부는 PR의 Workflow 상태로 외부 확인한다.

과거 Governance 이전 344-test 결과와 Governance 351-test 결과는 역사적 validation snapshot이며 최신 판정 authority가 아니다.

## 6. Evidence Boundary

자동 CI는 Repository 구조, Runtime Contract, Template/Guide/Projection/Scaffold 일관성을 검증한다. 다음을 대신하지 않는다.

- External Agent 반복 실행의 empirical semantic equivalence
- 일반 프로젝트 참여자의 first-use usability 관찰
- 실제 고객 프로젝트 production deployment
- Confirmed Business Authority가 포함된 Brownfield reconciliation empirical validation

## 7. 판정

Repository/Runtime/Document 구조 기준 판정은 `PASS_WITH_EVIDENCE_BOUNDARY`다.

최신 Commit Review에서 발견된 Tailoring direct fallback drift, Scaffold classification ambiguity, active metadata freshness 문제는 모두 보정되었고 회귀 테스트가 추가되었다. 최종 판정은 `framework/validation/LATEST_COMMIT_REVIEW_V110.md`의 구현 subject-head Evidence와 PR #67 current-head CI를 함께 근거로 한다.
