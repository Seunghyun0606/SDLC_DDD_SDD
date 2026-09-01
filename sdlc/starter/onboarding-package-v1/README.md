# SDLC Harness Onboarding Starter Pack v1 — P0 Candidate Wiring

> 목적: 고객/프로젝트에 SDLC Harness를 처음 적용할 때 필요한 입력자료, 설정, 분석, Skill화, 산출물 생성, Source 변경 제안까지를 시작 패키지로 제공한다.
>
> 기본 실행 모드: `PROPOSAL_ONLY`
>
> P0 Candidate에서는 `sdlc/config/artifact-profiles.yaml`, `sdlc/config/rq-boundary.yaml`, `sdlc/templates/stage-input-pack.yaml`, `sdlc/design/contracts/low-agent-execution-contract.md`를 실행 계약으로 추가한다.

## 0. P0 우선순위

기존 `04_artifact-selection-matrix.csv`의 `default_required`는 호환성 Catalog 값이다. 실제 별도 Human Artifact 생성 여부는 **Artifact Profile이 우선**한다.

```text
Artifact Profile
→ Legacy Artifact Catalog
→ Project Override
```

기본 Profile은 `STANDARD`다. 작은 프로젝트는 `LITE`, 규제/고위험/병렬개발은 `ENTERPRISE` 후보를 사용한다.

## 1. 고객사가 처음 제공할 것

### 공통 최소
1. 프로젝트 기본정보
2. 핵심 요구사항 원문
3. 가능한 범위의 업무정의/정책/프로세스 자료
4. 용어집 또는 주요 업무용어

### Brownfield일 때 추가
5. Source Repository 또는 분석 가능한 Snapshot
6. Build/Test 실행방법
7. Source/Profile 설정에 필요한 기술 정보

### Greenfield일 때
Source Snapshot은 요구하지 않는다. Preset/Architecture Decision을 시작점으로 사용한다.

## 2. 첫 실행 핵심 흐름

```text
Project/Profile
→ Source Requirement ID 보존
→ Requirement Boundary Candidate
→ Stage Input Pack
→ Business/Source Analysis
→ Engineering Design
→ Program/Task
→ Source Proposal/Change
→ Test/Verify
→ Reverse Sync/Knowledge
```

RQ Boundary가 모호하면 진행을 멈추는 대신 `UNRESOLVED + OPEN + Escalation`으로 유지한다. 다만 Canonical RQ로 조용히 확정하지 않는다.

## 3. 권장 입력 폴더

```text
customer-onboarding/
├ 00_project/
│  ├ project-onboarding.yaml
│  ├ artifact-selection.csv
│  └ glossary.csv
├ 01_business-sources/
│  ├ manifest.yaml
│  ├ requirements/
│  ├ policy/
│  ├ process/
│  └ reference/
├ 02_source-profile/       # Brownfield/Hybrid 조건부
├ 03_source/               # Brownfield/Hybrid 조건부
└ 04_results/
   ├ handoff/
   ├ business/
   ├ engineering/
   ├ verification/
   └ reverse-sync/
```

## 4. 기존 상세 자산

다음 파일은 계속 사용하되 P0 Contract를 우선한다.

- `01_customer-document-provision-guide.md`
- `02_business-source-manifest.yaml`
- `03_glossary-template.csv`
- `04_artifact-selection-matrix.csv`
- `05_source-profile.yaml`
- `06_existing-source-analysis-guide.md`
- `07_source-to-skill-guide.md`
- `08_business-analysis-6w-guide.md`
- `09_development-blueprint-guide.md`
- `10_source-generation-and-change-prompt.md`
- `11_validation-and-handoff-checklist.md`

## 5. Truth / Low-Agent 원칙

- `GIVEN`: 사용자가 직접 제공
- `OBSERVED`: Source/DB/Log에서 관찰
- `INFERRED`: 근거를 바탕으로 추론
- `CONFIRMED`: 권한 있는 사람/검증으로 확인
- `OPEN`: 아직 알 수 없음

Mechanical Validation은 Agent 판단보다 Validator를 우선한다.

금지:
- 고객 매뉴얼의 현행 화면 설명을 영구 Business Rule로 자동 승격
- Source의 현재 동작을 업무정책으로 자동 승격
- 이름/CRUD 유사성만으로 Legacy Requirement를 자동 Merge/Split
- 공통코드 값을 추정하여 실제 Source에 하드코딩
- 문서가 상세하다는 이유만으로 실제 Source Write 허용

## 6. P0 Validation

```text
python sdlc/scripts/validate_p0_contracts.py stage-pack <stage-input-pack.yaml>
python sdlc/scripts/validate_p0_contracts.py rq-boundary <requirement-boundary.yaml>
python sdlc/scripts/test_p0_contracts.py
```

검증 실패는 전체 프로젝트 정지가 아니라 잘못된 해당 Handoff/Publish/Write를 차단한다.

## 7. 첫 고객 테스트 권장 범위

```text
1개 업무 Scenario
→ Legacy Requirement ID 보존
→ Boundary Candidate
→ 3~10개 FR/BR/AC Candidate
→ 1개 고객 View
→ 1개 Engineering Design
→ 1~3개 PGM
→ Patch Proposal 또는 제한된 Change
→ Test Scenario
→ Reverse Sync Candidate
```

전 프로젝트 문서를 한 번에 넣지 않는다.
