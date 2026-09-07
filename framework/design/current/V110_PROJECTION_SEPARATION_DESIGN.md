# v1.10 Projection Separation — Current Design

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

Base: `SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0`

## 1. 설계 목표

v1.10의 핵심은 **Canonical 의미와 사람에게 보여주는 문서 토폴로지를 분리**하는 것이다.

```text
Requirement / Change / Evidence
            ↓
      Canonical Spec
       ↙        ↘
Engineering   Customer
Projection    Projection
```

Engineering과 Customer는 같은 Business/Project 의미를 근거로 하지만 문서 수, 순번, Template, Lifecycle을 서로 독립적으로 가진다.

## 2. 현재 Project 설정

Human-maintained 설정의 기준은 `.sdlc/project.yaml` 하나다.

기본 Profile:

- Engineering: `ENGINEERING_SDD_COMPACT`
- Customer: `CUSTOMER_STANDARD_3`
- PM: `PM_STANDARD`
- Customer Full 선택: `CUSTOMER_WATERFALL_FULL`

`documents.internal.profile`은 기존 입력을 읽기 위한 migration compatibility이며 신규 작성 기준이 아니다. `tailoring_runtime.py`를 직접 사용하는 경로도 `project_config.py`가 공개하는 현재 기본 Profile 상수를 사용하므로 누락된 Engineering 설정이 `STANDARD_5`로 되돌아가지 않는다.

## 3. Template 역할

현재 Stage Semantic Template의 유일한 원본은:

```text
sdlc/templates/semantic/
```

이다. 별도의 Stage Template alias/symlink는 사용하지 않는다.

역할은 다음과 같이 분리한다.

- `sdlc/templates/semantic/`: Stage에서 어떤 의미/Evidence를 작성할지
- `sdlc/templates/engineering/`: 개발자/Agent용 Engineering Projection
- `sdlc/templates/customer/`: 고객용 Projection
- `sdlc/templates/management/`: PM/관리 View
- `sdlc/templates/tailoring/standard/`: `STANDARD_3/5/STAGE_ORIENTED_FULL`용 Legacy/Formal Projection
- `sdlc/tailoring/standard/*.yaml`: 위 Artifact를 조립하는 Profile

## 4. Engineering 기본 구조

`ENGINEERING_SDD_COMPACT`는 Stage 문서 수를 그대로 노출하지 않고 업무/기능 단위 Living Spec으로 재구성한다.

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<TARGET>.md
└─ programs/<TARGET>.md  # 필요할 때만
```

`/work`는 AS-IS Evidence, 상세 설계, Program/Source Mapping, Development/Test/Verification을 보완한다. Requirement/Business Rule/TO-BE/Scope가 바뀌면 `/change`를 사용한다.

## 5. Customer Projection

Customer Projection은 Engineering Profile ID, Engineering 문서 수/순번/파일명에 의존하지 않는다.

기본 `CUSTOMER_STANDARD_3`은 3종, `CUSTOMER_WATERFALL_FULL`은 8종이며 프로젝트 Custom Profile로 N종을 정의할 수 있다.

`CUSTOMER_WATERFALL_FULL`은 표준 Config 선택만으로 사용할 수 있게 Standard Project Scaffold에 동봉하지만 기본 Customer Profile은 아니다.

Customer Final Review에서 사람이 표현을 다듬을 수 있지만 업무 의미 변경은 `/change`로 Canonical에 Round-trip한다.

## 6. Asset Boundary

Framework 개발 자산과 Project 배포 자산을 물리적으로 분리한다.

Project-facing:

- `docs/00_시작/`
- `.sdlc/project.yaml`
- `sdlc/scripts/`의 Project Runtime
- Standard Scaffold에 동봉된 선택형 command/Profile support
- 별도 선택 Extension
- `sdlc/design/contracts/`
- 선택된 Profile/Template/Agent Skill

Framework-only:

- `framework/**`
- `tests/**`
- `.github/**`

`docs/00_관리/`는 실제 Project가 실행 중 생성하는 PM/사용자 View 위치이며 Framework 검증보고서 보관소로 사용하지 않는다.

### 배포와 활성화의 구분

Project 자산은 세 가지 의미로 구분한다.

1. `PROJECT_REQUIRED`: 기본 실행에 필요하고 Standard Scaffold에 포함한다.
2. `PROJECT_BUNDLED_OPTIONAL`: Standard Scaffold에 파일은 포함하지만 선택한 command/Profile에서만 사용한다. 현재 `CUSTOMER_WATERFALL_FULL`, `component`, `impact-history`, `discover-impact`, `arch-check`, `metrics` 지원 자산이 해당한다.
3. `PROJECT_OPTIONAL`: Brownfield reverse, Document ingest, External tool처럼 별도 Extension 선택 시 추가한다.

이 구분은 `framework/ASSET_INVENTORY_V110.md`와 `project-scaffold-contract.json`이 함께 정의한다. 별도의 동적 Package Installer를 추가하지 않는다.

## 7. Framework 내부 Governance

현재 설계 metadata는 `framework/design/branch-version.yaml`, 현재 설계 설명은 본 문서가 담당한다.

과거 Baseline/Candidate/Review는 `framework/design/`의 역사 영역에 남긴다. 과거 active metadata나 폐기 inventory는 `framework/archive/`에 보존한다.

Framework Validation은 `framework/validation/`에 두며 Project Scaffold에는 배포하지 않는다.

정확한 최신 CI run id/test count 같은 휘발성 Evidence는 `branch-version.yaml`에 중복 고정하지 않는다. 최신 Review Evidence 문서와 PR current-head CI를 외부 검증 근거로 사용한다.

## 8. v1.9 관계

v1.10은 v1.9 Branch를 Base로 하며 현재 비교에서 v1.9의 변경을 모두 포함하고 behind 0 상태를 유지한다. v1.9를 최신 SoT로 되돌리지 않는다.

v1.9 당시 active branch metadata는 Archive snapshot으로 보존한다.

## 9. Evidence Boundary

자동 CI/Regression이 확인하는 것은 Repository 구조, Runtime 계약, Project Scaffold, Projection 독립성, Guide/Template 일관성이다.

다음은 별도 실제 관찰 Evidence가 필요하다.

- External Agent 반복 실행의 의미 동등성
- 일반 프로젝트 참여자의 first-use usability
- 실제 고객 프로젝트 production deployment
- Confirmed Business Authority가 포함된 Brownfield reconciliation empirical validation

따라서 CI PASS만으로 위 항목을 완료했다고 주장하지 않는다.
