# v1.10 Projection Separation 최종 검증 보고서

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

Base Branch: `SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`

검증 목적은 **Canonical 의미와 Engineering/Customer Projection의 문서 토폴로지를 분리하고, 실제 프로젝트 배포 자산과 Framework 개발 자산의 경계를 명확히 했는지**를 자동 회귀와 구조 검증으로 확인하는 것이다.

## 1. 검증 원칙

- `main`에는 merge하지 않는다.
- Draft PR #67은 validation-only이며 base는 v1.9 Branch다.
- 문서에 적힌 PASS/READY 표현을 선행 근거로 사용하지 않고 실제 GitHub Actions 결과를 근거로 판정한다.
- 자동화된 CI가 검증하지 못하는 External Agent empirical repeatability, 실제 사용자 usability, production deployment는 별도 Evidence로 남긴다.

## 2. 주요 구현 검증 결과

| Scenario | Result | Evidence | Residual Risk |
|---|---|---|---|
| Engineering 기본 Profile이 Compact SDD 중심인가 | PASS | `ENGINEERING_SDD_COMPACT`, Project Config resolution regression | Legacy Profile 사용 프로젝트는 명시적 compatibility 선택 필요 |
| `documents.engineering.profile`과 legacy `documents.internal.profile` 우선순위가 명확한가 | PASS | `project_config.py`, `test_engineering_profile_resolution_prefers_new_key_and_preserves_legacy_alias` | legacy alias는 제거 전까지 호환 레이어로 유지 |
| Customer Projection이 Engineering Profile/파일명/문서 수를 읽지 않는가 | PASS | `customer_projection_runtime.py`, `test_customer_settings_do_not_resolve_engineering_profile` | Legacy input의 Stage fallback은 compatibility 목적상 유지 |
| Customer 문서 3종/8종 분리가 Engineering 토폴로지와 독립적인가 | PASS | `CUSTOMER_STANDARD_3`, `CUSTOMER_WATERFALL_FULL`, projection invariant tests | 고객별 N종 Custom Profile 품질은 개별 프로젝트 책임 |
| Change Level이 Canonical 의미를 바꾸지 않고 Projection 선택과 분리되는가 | PASS | `validate_canonical_projection_invariant.py`, invariant regression | Change Level 정책 자체의 현장 적합성은 프로젝트별 검토 필요 |
| Engineering/Customer Projection lifecycle이 stale/manual edit/final review를 구분하는가 | PASS | `projection_lifecycle_runtime.py`, v1.10 lifecycle tests | 외부 편집기/병렬 편집 정책은 운영 규칙 필요 |
| Engineering Projection 생성이 shared lifecycle을 사용하는가 | PASS | `tailored_work.py`, `test_tailored_work_registers_engineering_projection_through_shared_lifecycle` | 없음(현재 자동 회귀 범위) |
| Customer 최종 검토 문구가 Canonical 변경 시 자동 덮어쓰기 되지 않는가 | PASS | `test_customer_final_review_is_preserved_when_canonical_changes` | 재생성 후 Human reconciliation 절차는 사용자 운영 필요 |
| Project Scaffold가 Framework/Test/Pilot/Legacy-default 자산을 제외하는가 | PASS | `project-scaffold-contract.json`, `test_asset_boundary_v110.py`, scaffold materialization test | 선택 Extension 조합은 개별 프로젝트에서 추가 검증 필요 |
| Framework-only 설계이력/Pilot/Validation/Sample이 물리적으로 분리됐는가 | PASS | `framework/` 구조, compare result, asset-boundary tests | `tests/`, `.github/`는 CI convention 때문에 최상위 유지 |
| `sdlc/guides` 중복이 제거되고 `docs/00_시작`이 Guide SoT인가 | PASS | 삭제/이동 diff, Docs quality workflow | 과거 외부 링크는 compatibility notice가 필요한 경우가 있음 |
| Customer Projection 기본 Config 이름이 runtime dependency임을 드러내는가 | PASS | `customer-document-profile.json`, runtime default, old `.example` symlink alias | Legacy 경로는 compatibility 기간 동안 존재 |
| 기존 v1.9 동작/계약 호환성이 유지되는가 | PASS | Production Readiness의 v1.9 tailoring/intake/contract consistency regression | 장기적으로 legacy wrapper 제거 시 별도 migration 검증 필요 |
| Greenfield E2E가 유지되는가 | PASS | Greenfield Work Executor E2E workflow | Validation fixture 기반이며 실제 외부 Agent empirical pass와 동일하지 않음 |
| Public Brownfield Pilot가 유지되는가 | PASS | Public Brownfield Pilot workflow | 특정 public-pilot 범위의 통합 검증이며 모든 기술 스택을 대표하지 않음 |

## 3. 자동 검증 Evidence

검증 Head `10869c9e3ecef2cc394579786e925ad84e886650`에서 다음 GitHub Actions가 모두 성공했다.

- P0 P1 Production Readiness #275 — SUCCESS
- Worklist sync quality #1143 — SUCCESS
- Docs quality #439 — SUCCESS
- Greenfield Work Executor E2E #285 — SUCCESS
- Public Brownfield Pilot #298 — SUCCESS

Production Readiness 세부 성공 항목:

- Python syntax check
- v1.10 Projection Separation regression
- v1.9 tailoring/intake/contract consistency regression
- integrated project-config/intake behavioral regression
- existing core runtime regressions
- harness structure validation
- document experience validation

Full unittest discovery는 331 tests를 성공했다.

> 이 보고서 파일 추가 이후의 최종 Branch Head도 동일 Workflow를 다시 실행해 확인한 뒤 PR 본문 Head를 갱신한다.

## 4. Asset Boundary 판정

### Project-facing SoT

- User Guide: `docs/00_시작/`
- Project Config: `.sdlc/project.yaml`
- Runtime: `sdlc/scripts/`의 Project Runtime + 선택 Extension
- Runtime Contract: `sdlc/design/contracts/`
- Standard Projection Profile/Template: `sdlc/tailoring/standard/`, `sdlc/templates/`

### Framework-only

- `framework/design/`
- `framework/management/`
- `framework/pilots/`
- `framework/samples/`
- `framework/validation/`
- `tests/`
- `.github/`

### Compatibility-only

- `sdlc/validation` → `framework/validation/assets`
- `sdlc/config/customer-document-profile.example.json` → `customer-document-profile.json`
- `runtime_config_v19.py`
- Legacy tailoring profiles/templates

## 5. Overengineering Audit

이번 정리에서는 새로운 Packaging Engine, 별도 Customer Assembly Engine, 별도 Lifecycle 구현을 추가하지 않았다.

- 배포 선택은 기존 `build_project_scaffold.py` + `project-scaffold-contract.json`을 확장했다.
- Project Config 고수준 규칙은 `project_config.py` 하나로 모으고 `runtime_config_v19.py`는 wrapper로 축소했다.
- Projection lifecycle은 `projection_lifecycle_runtime.py` 하나를 공유한다.
- Customer topology는 Customer Profile에서만 정의하며 Engineering mapping registry를 추가하지 않았다.
- Framework 자산 이동 시 복제 대신 rename/symlink/compatibility notice를 우선했다.

따라서 v1.10의 핵심 방향은 **새 계층 추가보다 기존 경계의 명시화와 중복 제거**다.

## 6. 최종 판정 기준

자동화 기준 최종 판정은 다음을 모두 만족할 때 `PASS_WITH_EVIDENCE_BOUNDARY`로 기록한다.

1. 최신 Branch Head의 5개 PR Workflow가 모두 SUCCESS
2. Draft PR이 open/draft/unmerged 상태
3. PR base가 `SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`
4. Branch가 base 대비 behind 0
5. `main` merge 없음

External Agent empirical repeatability, 실제 프로젝트 사용자 관찰 usability, production deployment validation은 이 판정 범위 밖이다.
