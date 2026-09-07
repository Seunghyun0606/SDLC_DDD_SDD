# SDLC Framework 개발 자산

이 디렉터리는 **실제 프로젝트에 배포하지 않는 SDLC Harness Framework 개발/검증/설계이력 자산**의 명시적 경계다.

## 1. Project-facing Source of Truth

- 사용자 진입점: `docs/00_시작/START_HERE.md`
- Human-maintained Project Config: `.sdlc/project.yaml`
- 프로젝트 실행 Runtime: `sdlc/scripts/`의 Project Runtime + 기본 동봉 선택형 command support + 별도 선택 Extension
- Runtime Contract: `sdlc/design/contracts/`
- Stage Semantic Template: `sdlc/templates/semantic/`
- Engineering/Customer/PM Projection: 선택된 Profile/Template

`framework/` 아래 자산은 모두 `FRAMEWORK_ONLY`이며 Project Scaffold에 배포하지 않는다.

### Project Runtime 자산의 세 가지 배포 의미

- `PROJECT_REQUIRED`: 기본 실행 경로에 필요하며 Standard Scaffold에 포함한다.
- `PROJECT_BUNDLED_OPTIONAL`: Standard Scaffold에 파일은 동봉하지만 해당 command/Profile을 선택할 때만 사용한다. 예: `CUSTOMER_WATERFALL_FULL`, `component`, `discover-impact`, `arch-check`, `metrics` 지원 자산.
- `PROJECT_OPTIONAL`: Brownfield reverse, Document ingest, 외부도구처럼 별도 선택 시 추가하는 Extension이다.

동봉 여부와 기능 활성화 여부를 같은 의미로 취급하지 않는다.

## 2. Framework 구조

```text
framework/
├─ README.md
├─ ASSET_INVENTORY_V110.md
├─ design/
│  ├─ README.md
│  ├─ branch-version.yaml
│  ├─ CHANGELOG.md
│  ├─ current/              # 현재 v1.10 설계 요약
│  ├─ baselines/            # 역사 Full Design snapshot
│  ├─ candidates/           # 역사 Candidate/Delta
│  ├─ reviews/              # 역사 Review
│  ├─ validations/          # 역사 Design-era validation
│  └─ session/              # 현재 Session governance/lineage
├─ archive/                 # superseded metadata/inventory snapshot
├─ management/              # Framework 자체 작업목록/관리자료
├─ pilots/                  # Framework Pilot/history
├─ samples/                 # 비교/교육/검증 fixture
└─ validation/              # 현재 검증 보고서 + validation assets

tests/                      # CI convention 때문에 저장소 최상위 유지, FRAMEWORK_ONLY
.github/                    # Framework CI, FRAMEWORK_ONLY
sdlc/design/contracts/      # Runtime dependency, Project 배포 대상
```

## 3. Design와 Archive의 차이

`framework/design/`은 **설계 자체의 현재 기준과 진화 이력**을 관리한다.

현재 설계는 다음 순서로 본다.

1. `framework/design/branch-version.yaml`
2. `framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md`
3. `framework/design/CHANGELOG.md`
4. `framework/ASSET_INVENTORY_V110.md`
5. `framework/validation/`의 v1.10 검증 보고서

`framework/archive/`는 과거 active metadata, 폐기 inventory, migration snapshot처럼 **현재 위치에 남아 있으면 최신으로 오해될 수 있는 자산**을 보존한다. Archive는 현재 SoT가 아니다.

## 4. 현재 v1.10 주요 경계

- v1.10이 현재 Framework source이며 v1.9 변경을 모두 포함한다.
- Stage Template은 `sdlc/templates/semantic/`이 유일한 원본이며 별도 Stage Template alias/symlink는 없다.
- `sdlc/templates/tailoring/standard/`는 `STANDARD_3/5/STAGE_ORIENTED_FULL`용 Legacy/Formal Projection Template이다.
- Engineering 기본값은 모든 Runtime 진입 경로에서 `ENGINEERING_SDD_COMPACT`를 사용한다. `STANDARD_5`는 신규 기본 fallback이 아니다.
- `CUSTOMER_WATERFALL_FULL`과 경량 Enhancement command support는 Standard Scaffold에 동봉되지만 선택 전에는 활성 기능으로 간주하지 않는다.
- Brownfield reverse/Document ingest/External tool Extension은 동봉 선택형과 구분하여 별도 선택 자산으로 유지한다.
- Guide SoT는 `docs/00_시작/`이다. `sdlc/guides`는 제거됐다.
- `docs/00_관리/`는 Framework 보고서 보관소가 아니라 프로젝트 실행 중 생성되는 PM/사용자 View 위치다.
- `framework/validation/`은 Framework 검증 보고서와 fixture/provider를 보관한다.

## 5. Compatibility 자산

새로운 용어/경로 통합을 위해 **새 compatibility symlink를 만들지 않는 것**을 기본으로 한다. 다만 v1.10 이전 Contract/Test와의 별도 호환 부채로 이미 존재하는 경로는 Asset Inventory에 명시하고 Project Scaffold에서는 제외한다.

현재 별도 compatibility debt:

- `sdlc/validation` → Framework validation assets를 가리키는 과거 검증 경로
- `sdlc/config/customer-document-profile.example.json` → 정식 Customer config 이름 전환 전의 과거 참조 경로
- `runtime_config_v19.py` → v1.9 설정 진입점 thin wrapper

이 항목들은 Stage Template terminology와는 별개이며 신규 Runtime/Guide는 정식 경로를 사용한다.

세부 파일별 분류와 residual debt는 `framework/ASSET_INVENTORY_V110.md`를 따른다. 최신 커밋 단위 리뷰와 current-head CI 근거는 `framework/validation/LATEST_COMMIT_REVIEW_V110.md`와 PR #67에서 확인한다.
