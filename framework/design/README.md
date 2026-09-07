# Framework Design Governance

`framework/design/`은 **SDLC Harness Framework의 현재 설계 기준과 설계 진화 이력**을 보관한다. 실제 Project Runtime Contract는 `sdlc/design/contracts/`에 남아 있으며, `framework/design/` 자체는 Project Scaffold에 배포하지 않는다.

## 1. 현재 설계 Source of Truth

현재 v1.10을 설명하는 우선순위는 다음과 같다.

1. `framework/design/branch-version.yaml` — 현재 Branch/Version/설계 상태 metadata
2. `framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md` — v1.10 현재 설계 요약
3. `framework/design/CHANGELOG.md` — 버전 간 설계 변화
4. `framework/ASSET_INVENTORY_V110.md` — 현재 자산/배포 경계
5. `framework/validation/*V110*.md` — 자동 검증 및 판정 근거
6. `sdlc/design/contracts/` — 실제 Runtime이 읽는 executable contract

현재 동작 판단에서 과거 Baseline/Candidate/Validation 문서를 우선하지 않는다.

## 2. 역사 설계 자산

```text
framework/design/
├─ README.md
├─ branch-version.yaml       # ACTIVE
├─ CHANGELOG.md              # ACTIVE
├─ current/                  # ACTIVE design summary
├─ baselines/                # HISTORICAL full-design snapshots
├─ candidates/               # HISTORICAL design deltas / RC proposals
├─ reviews/                  # HISTORICAL design reviews
├─ validations/              # HISTORICAL design-era validation notes
└─ session/                  # ACTIVE session governance + lineage
```

`baselines/`, `candidates/`, `reviews/`, `validations/`는 과거 설계 의사결정의 근거로 유지하지만 **현재 v1.10의 동작을 설명하는 SoT가 아니다.**

## 3. Archive와의 차이

- `framework/design/`에 남는 것: 설계 진화 자체를 설명하는 Baseline, Candidate, Review, Validation.
- `framework/archive/`로 가는 것: 과거 active metadata, 폐기된 inventory, migration snapshot처럼 현재 경로에 남아 있으면 최신 상태로 오해되는 자산.

예: v1.9 당시 active `branch-version.yaml`은 v1.10 active metadata로 교체하기 전에 `framework/archive/design-metadata/branch-version-v1.9.0.yaml`로 보존한다.

## 4. 수정 원칙

- `branch-version.yaml`, `CHANGELOG.md`, `current/`, `session/`은 현재 버전 변경 시 함께 갱신한다.
- 과거 Baseline/Candidate를 최신 설계처럼 다시 작성하지 않는다.
- 역사 문서의 broken path를 고칠 필요가 있으면 의미 변경 없이 최소 migration만 수행한다.
- Validation PASS 문구는 실제 CI/검증 Evidence 범위를 넘겨 해석하지 않는다.
- `main` merge는 이 Session에서 금지한다.
