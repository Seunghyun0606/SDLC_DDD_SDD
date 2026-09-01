# SDLC Harness Onboarding Starter Pack v1

> 목적: 고객/프로젝트에 SDLC Harness를 처음 적용할 때 필요한 입력자료, 설정, 분석, Skill화, 산출물 생성, Source 변경 제안까지를 하나의 시작 패키지로 제공한다.
>
> 기본 실행 모드: `PROPOSAL_ONLY`
>
> 이 Starter Pack은 Candidate A/B 선택과 독립적인 Onboarding 입력 계약이다. 실제 Source Write / Merge / Release는 프로젝트별 안전성 검증 및 명시적 허용 전에는 수행하지 않는다.

## 1. 고객사가 처음 제공할 것

1. 업무 원본문서 3~10개: 요구사항 Excel, 업무정의서/정책서, 화면/프로세스 PPT, 운영매뉴얼/회의록
2. 용어집 또는 주요 업무용어 20~100개
3. 이번 프로젝트에서 만들고 싶은 산출물 선택표
4. Source/Profile 설정표
5. Brownfield Source Repository 또는 분석 가능한 Snapshot
6. 빌드/Test 실행방법
7. 실제 코드/권한/공통코드/DB 정보 중 공개 가능한 범위

## 2. 권장 폴더 구조

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
│  ├ manuals/
│  ├ legacy-design/
│  ├ meeting-notes/
│  └ reference/
├ 02_source-profile/
│  └ source-profile.yaml
├ 03_source/
│  └ <repository or snapshot>
└ 04_results/
   ├ extraction/
   ├ business/
   ├ customer/
   ├ engineering/
   ├ skills/
   └ verification/
```

## 3. 실행 순서

```text
STEP 0  프로젝트 기본정보/산출물 선택
STEP 1  고객 원본문서 Catalog/Manifest 작성
STEP 2  용어집 작성
STEP 3  Source Profile 작성
STEP 4  SoP/요구사항 Extraction
STEP 5  6W 업무정의 + RQ/FR/BR/AC 후보 생성
STEP 6  고객 검토용 산출물 생성
STEP 7  Existing Source 분석
STEP 8  반복되는 Source/업무 패턴 Skill Candidate 생성
STEP 9  Development Blueprint 생성
STEP 10 Source Change Proposal 생성
STEP 11 Test/Trace/OPEN/STALE 확인
STEP 12 실제 Write 허용 여부 별도 판단
```

## 4. 핵심 파일

| 파일 | 목적 |
|---|---|
| `01_customer-document-provision-guide.md` | 고객 원본문서 제공방법 |
| `02_business-source-manifest.yaml` | 문서 유형/권위/범위/유효기간 |
| `03_glossary-template.csv` | 용어/동의어/공통코드 |
| `04_artifact-selection-matrix.csv` | 프로젝트별 산출물 선택 |
| `05_source-profile.yaml` | Brownfield Source 구조/Convention |
| `06_existing-source-analysis-guide.md` | 기존 Source 분석 |
| `07_source-to-skill-guide.md` | 반복 패턴 Skill화 |
| `08_business-analysis-6w-guide.md` | 6W 기반 업무분석 |
| `09_development-blueprint-guide.md` | UI/CRUD/Logic/SQL/Data 상세설계 |
| `10_source-generation-and-change-prompt.md` | 산출물→Source Proposal Prompt |
| `11_validation-and-handoff-checklist.md` | Gate/검증 |
| `skills/*` | Agent 실행지침 |
| `templates/*` | 표준 산출물 Template |

## 5. Truth 원칙

- `GIVEN`: 사용자가 직접 제공
- `OBSERVED`: Source/문서에서 관찰
- `INFERRED`: 근거를 바탕으로 추론
- `CONFIRMED`: 권한 있는 사람/검증으로 확인
- `OPEN`: 아직 알 수 없음

금지:
- 고객 매뉴얼의 현행 화면 설명을 영구 Business Rule로 자동 승격
- Source의 현재 동작을 업무정책으로 자동 승격
- 공통코드 값을 추정하여 실제 Source에 하드코딩
- 문서가 상세하다는 이유만으로 실제 Source Write 허용

## 6. 첫 고객 테스트 권장 범위

```text
1개 업무 Scenario
→ 3~10개 FR
→ 3~10개 BR
→ 1개 고객 기능정의서
→ 1~3개 PGM
→ 1개 Development Blueprint
→ Patch Proposal
→ Test Scenario
```

전 프로젝트 문서를 한 번에 넣지 않는다.

## 7. 성공 기준

- 고객이 6W/Scope/Rule/AC를 이해하고 검토할 수 있다.
- 개발자가 Blueprint만 보고 추가 질문 목록과 수정 대상 Source를 식별할 수 있다.
- 모든 중요한 판단이 원본문서/Source 위치로 역추적된다.
- 모르는 값이 `OPEN`으로 남는다.
- Source 변경 제안이 기존 Architecture/Convention을 보존한다.
- 실제 Write 전 필요한 결측정보가 명확하게 보인다.
