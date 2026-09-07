# v1.10 최신 Commit 포함 통합 Review

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

Review 대상은 v1.10 전체 변경과 최근 Framework Governance 연속 Commit을 포함한다.

- `b4796bb8c224d8d2ff0b84bde7d5fcd508edc702` — Framework Design/Archive governance 정렬
- `da4c9c6a9f695287d57f54c0cb50ade0d3c2f5f5` — inherited validation boundary 보존
- `93ee8b6574538f10e8b4a7f03a2957211a5c355c` — governance regression 보정
- `d96611caa2f2477c34ca9607c27c824710ed82c8` — governance validation evidence 기록

## 1. Review 범위

- Project Config / Tailoring Runtime 기본값
- Engineering / Customer Projection 독립성
- Template 역할과 Semantic root
- Project Scaffold 실제 파일 선택과 Asset Inventory 분류
- Framework Design / Archive current/history 경계
- Validation metadata freshness와 Evidence boundary
- 기존 v1.6/v1.9/v1.10 회귀 호환성

## 2. Review에서 발견된 Gap

### P1 — Tailoring Runtime direct fallback drift

`project_config.py`의 현재 Engineering 기본값은 `ENGINEERING_SDD_COMPACT`지만 `tailoring_runtime.py` 내부 fallback이 `STANDARD_5`에 남아 있었다.

일반 Harness 경로에서는 Config normalization으로 가려질 수 있으나 Tailoring Runtime 직접 사용 또는 불완전 Project dict에서는 Legacy 기본값으로 되돌아갈 수 있었다.

조치: Tailoring Runtime fallback을 `runtime_config_v19.py`가 re-export하는 current `DEFAULT_ENGINEERING_PROFILE`, `DEFAULT_CUSTOMER_PROFILE`, `DEFAULT_PM_PROFILE` 상수로 통일한다.

### P1 — Scaffold 분류와 실제 배포 의미 불일치

Asset Inventory는 일부 Enhancement Runtime과 `architecture-rules.json`을 `PROJECT_OPTIONAL`로 분류했지만 `project-scaffold-contract.json`의 `add_required_files`는 이 파일들을 Standard Scaffold에 실제 동봉하고 있었다. `CUSTOMER_WATERFALL_FULL`도 Config로 즉시 선택 가능하도록 기본 Scaffold에 동봉된다.

이 파일들을 제거하면 현재 Public Harness command와 Config-only Profile 전환을 위해 별도 Installer가 필요해진다. 신규 Packaging Engine을 추가하지 않고 실제 동작을 정확히 표현하도록 `PROJECT_BUNDLED_OPTIONAL` 분류를 도입한다.

- 파일은 Standard Scaffold에 동봉
- 기능/Profile 활성화는 선택
- Brownfield reverse / Document ingest / External tool Extension은 계속 별도 `PROJECT_OPTIONAL`

### P2 — Active branch metadata에 과거 CI snapshot 중복

`framework/design/branch-version.yaml`은 Current SoT인데 Governance 이전 Head와 344 test count를 embedded snapshot으로 가지고 있었다. 값 자체는 historical field였지만 Current metadata에서 최신 CI처럼 오해될 여지가 있다.

Commit SHA를 동일 Commit 안에서 current head로 기록하는 것은 자기참조가 되므로 Active metadata는 exact SHA/run/test count를 직접 소유하지 않는다.

조치:

- Active metadata는 본 Review Evidence와 PR #67 current-head CI를 가리킨다.
- exact 검증 대상 Commit/run/test count는 이 Review 문서에 외부 Evidence snapshot으로 기록한다.
- 최종 Head CI는 PR의 current-head Workflow 상태로 확인한다.

## 3. 유지되는 핵심 판정

- Canonical은 Business/Project 의미 SSOT다.
- Engineering 기본은 `ENGINEERING_SDD_COMPACT`다.
- Customer 기본은 `CUSTOMER_STANDARD_3`이며 Engineering topology와 독립이다.
- Stage Semantic Template 원본은 `sdlc/templates/semantic/` 하나다.
- `STANDARD_3/5/STAGE_ORIENTED_FULL`은 Legacy/Formal Projection compatibility다.
- `framework/design/current/`은 현재 설계, baselines/candidates/reviews/validations는 역사 설계다.
- `framework/archive/`는 superseded active metadata/inventory snapshot만 보존한다.
- `main` merge는 금지한다.

## 4. 추가 자동 회귀

`tests/test_latest_commit_review_v110.py`를 추가해 다음을 고정한다.

1. Direct Tailoring fallback도 `ENGINEERING_SDD_COMPACT`를 사용한다.
2. Standard Scaffold의 bundled optional 분류가 실제 파일 선택과 일치한다.
3. Brownfield/Document-ingest 등 true optional Extension이 기본 Scaffold에 섞이지 않는다.
4. Active metadata가 휘발성 과거 Head/test count를 Current authority로 내장하지 않는다.
5. Asset Inventory가 bundled optional과 separately optional을 구분한다.

## 5. CI Evidence

본 보정 Commit의 자동 CI가 완료된 뒤 이 section에 **검증 대상 Commit SHA, 5개 Workflow run, 전체 unittest count**를 기록한다.

현재 상태: `REMEDIATION_IMPLEMENTED_CI_PENDING`

## 6. Evidence Boundary

이 Review와 CI는 Repository/Runtime/Contract/Scaffold/Guide/Framework Governance 정합성을 검증한다. 다음을 자동 PASS로 확대 해석하지 않는다.

- External Agent 반복 실행 의미동등성
- 일반 프로젝트 참여자의 first-use usability
- 실제 고객 production deployment
- Confirmed Business Authority가 있는 Brownfield reconciliation empirical validation
