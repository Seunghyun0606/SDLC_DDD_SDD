# SDLC Harness 종합 Red Team / Usability / Low-Agent Review v1

- 기준 Branch: `SDLC_DESIGN_SESSION_SECOND/base`
- 검토 일자: 2026-09-01
- 검토 관점: Architecture Red Team + 실제 프로젝트 Persona + Low-capability Agent
- Pilot 입력: `요구사항목록.xlsx`의 `근태마감` 영역(REQ_TM_TE016~REQ_TM_TE031), focal item `REQ_TM_TE017 일근태입력/마감 조회`
- 원칙: 현재 구조를 옹호하지 않고 실제 고객 프로젝트에서 실패할 지점을 우선 확인한다.

---

# 0. 현재 Architecture 재구성

## 0.1 실제 Repository에서 확인한 현재 구조

현재 `base`는 크게 다음 계층으로 구성된다.

1. 사용자 Quick Start / Guide
   - `sdlc/README.md`
   - `sdlc/guides/01_SDLC_전체가이드.md`
   - `sdlc/guides/02_SKILL_사용가이드.md`
   - `sdlc/guides/03_TEMPLATE_산출물가이드.md`
   - `sdlc/guides/04_HARNESS_커스터마이징가이드.md`
2. Current Full Design
   - `sdlc/design/baselines/AI_SDLC_Harness_Full_Design_v1.5.1.md`
3. Onboarding Starter Pack
   - `sdlc/starter/onboarding-package-v1/*`
4. Project/Preset Config
   - `sdlc/config/project-profile.example.yaml`
   - `sdlc/config/worklist-columns.yaml`
   - `sdlc/custom/presets/brownfield-auto.yaml`
   - `sdlc/custom/presets/greenfield-default.yaml`
5. 과거 Candidate / Validation / Consolidation 기록
   - `sdlc/design/experiments/*`
   - `sdlc/design/validation/*`
   - `sdlc/design/consolidation/*`
6. 실제 프로젝트 사용자 View
   - `docs/00_관리/전체작업목록.md`

## 0.2 전체 흐름

```text
고객 입력
→ Intake / Onboarding
→ Business Source Catalog / Extraction
→ 6W Business Definition
→ RQ Boundary / FR / BR / AC
→ Customer Functional Specification / Process
→ Source Discovery / Impact
→ Functional Design / Development Blueprint
→ PGM / TASK
→ Source Change
→ Test
→ Verify
→ Knowledge Promotion
→ Change / STALE
```

최신 Baseline의 사용자 UX는 이를 `/work /change /check`로 숨긴다.

## 0.3 단계별 입력/산출물

| 단계 | 입력 | 산출물 | 주요 사용자 | 다음 단계 | 필수 여부 | 비고 |
|---|---|---|---|---|---|---|
| Project Setup | 프로젝트 정보, 기존 자산 또는 Preset | Project Profile / Overlay | Harness 관리자 | Intake | MUST | 현재 Starter 기본값은 Brownfield 편향 |
| Intake | 요구사항 원문, Excel/PPT/Word | Requirement / Source Catalog | PM/BA | Extraction | MUST | Legacy ID 보존 규칙 필요 |
| Extraction | 원본문서, Manifest, Glossary | Evidence Fragment / Candidate | BA/Agent | 6W/RQ | RECOMMENDED | Raw source locator 유지 필요 |
| Business Definition | Evidence Fragment | 6W, Scope, FR/BR/AC Candidate | BA/Customer | Customer Review | RECOMMENDED | 별도 문서보다 분석 문서 Section화 가능 |
| Customer Review | 6W/RQ/FR/BR/AC | Customer Functional Spec | Customer/BA/PM | Impact/Design | MUST for customer-facing | 사람이 직접 중복 작성하면 안 됨 |
| Process | 업무 흐름 | AS-IS/TO-BE Process | BA/Designer | Impact/Design | CONDITIONAL | Process-heavy RQ에서만 필요 |
| Discovery | RQ/FR/BR + Source Profile | Source Analysis Result | Designer/Dev/Agent | Impact | BROWNFIELD MUST | Greenfield에서는 N/A |
| Impact | Requirement + Evidence | Business/Functional/Technical Impact | Designer/Dev | Design | MUST(Std) | Greenfield simple change는 축소 가능 |
| Functional/Engineering Design | Requirement/Impact | Functional Design / Blueprint | Designer/Dev | PGM | MUST(Std) | 두 문서 역할 중복 가능성 큼 |
| Program | Engineering Design | PGM Spec / TASK | Dev/PM | Development | CONDITIONAL | Simple change는 Full PGM Spec 불필요 |
| Development | TASK/PGM/Context Pack | Source + Implementation Result | Dev | Test | MUST | Source write guard 필요 |
| Test | AC/PGM/Source | TC/Test Result | QA/Dev | Verify | MUST | AC→TC deterministic check 가능 |
| Verify | RQ/AC/Test/Source | Verification Result | QA/PM/Customer | Promotion | MUST | 미수행 Test 명시 |
| Promotion | Verified artifacts | Knowledge | BA/Dev/Ops | Next RQ | RECOMMENDED | 내부 데이터 중심 |
| Change | CR 또는 Source Diff | STALE Candidate / Review | PM/Dev/Change mgr | 재분석 | MUST when changed | Source→Doc reverse path가 미완성 |

---

# A. Executive Verdict

## CONDITIONALLY READY

1. Core 개념은 Brownfield/Greenfield/Hybrid, Canonical Trace, Quick Start, Overlay를 갖춰 Pilot 기반은 충분하다.
2. 하지만 Starter Pack은 최신 Baseline보다 Brownfield-first이며 15개 Artifact 중 13개를 기본 Required로 두어 실사용 복잡도가 높다.
3. RQ Boundary, Source Discovery, Impact, Reverse Sync의 결정 규칙이 부족해 Agent 성능 의존성이 높다.
4. Overlay는 선언되어 있으나 Tool/MCP Provider Interface와 Config-vs-Adapter 경계가 실제 계약으로 충분히 구현되지 않았다.
5. 고객 Pilot 전에는 Artifact Profile, Stage Input Pack, Low-Agent Procedure/Validator, Reverse Sync Contract를 최소 보강해야 한다.

---

# B. 10개 평가 Scorecard

| # | 평가항목 | 점수 /10 | 핵심 문제 |
|---|---|---:|---|
| 1 | Over-engineering | 5.0 | Starter 기본 산출물 13/15 Required, 6W/Requirement/Customer Spec/Design 간 중복 |
| 2 | Greenfield / Brownfield | 7.0 | Core는 공통이지만 Starter config/profile은 Brownfield 및 Java/MyBatis/Oracle 편향 |
| 3 | Customizing | 6.0 | Overlay 개념은 좋으나 실제 Schema/Adapter boundary와 예시 부족 |
| 4 | Participant Usability | 6.0 | Quick Start는 좋지만 Starter/Baseline/Validation 자료의 현재성 경계가 약함 |
| 5 | Korean Readability | 7.0 | 사용자 View 한글화는 개선, YAML/내부 필드 Dictionary 부족 |
| 6 | MCP / Tool Extensibility | 4.0 | Provider/Capability Interface가 Current Baseline의 실행 계약으로 없음 |
| 7 | Stage Continuity | 6.0 | Canonical 관계는 강하나 Artifact 간 Handoff/필드 변환 규칙이 불충분 |
| 8 | Customer Deliverable | 7.0 | Customer Spec 범위는 좋으나 작성 Contract/결정 상태/화면 항목 구조화 부족 |
| 9 | Source ↔ Documentation Reverse Sync | 4.0 | `/change`/STALE 개념은 있으나 Source Diff→Semantic Change→Doc 영향 계약이 없음 |
| 10 | Low-capability Agent Readiness | 4.5 | Procedure/Stop/Escalation/Validator 부족, RQ/Impact 단계 모델 의존 |

**총점: 56.5 / 100**

Critical warning:
- Low-capability Agent Readiness < 5
- MCP/Tool Extensibility < 5
- Reverse Sync < 5

단순 평균과 무관하게 첫 고객 Pilot은 Guard 보강 전 완전 Ready로 볼 수 없다.

---

# C. Top 10 문제

| Severity | 문제 | 실제 실패 방식 | 우선 개선 |
|---|---|---|---|
| P0 | Legacy Requirement Row → Canonical RQ Boundary 규칙 부족 | 같은 Excel을 Agent A는 16 RQ, Agent B는 1 RQ+16 FR로 생성 | `source_requirement_id` 보존 + RQ split/merge decision rule |
| P0 | Low-Agent Skill의 Stop/Escalation Rule 부족 | Source 없음에도 임의 영향분석, OPEN 유실 | 공통 Skill Procedure Contract + fail-safe escalation |
| P0 | Source→Documentation Reverse Sync 미완성 | Hotfix/Procedure 변경 후 BR/AC/PGM 문서가 현재성을 잃음 | Source Diff semantic classification contract |
| P1 | Artifact 기본 Required 과다 | 작은 RQ가 10개 이상 문서 생성/수정 | Lite/Standard/Enterprise Profile |
| P1 | Starter와 최신 Baseline의 Project Mode 불일치 | Baseline은 AUTO/Greenfield, Starter는 `mode: BROWNFIELD` | Starter mode=AUTO + mode-specific required inputs |
| P1 | Source Profile이 Java/JSP/MyBatis/Oracle에 하드코딩 | Spring Boot/JPA/Kotlin/Kafka에 Template 수정 필요 | stack-neutral core + adapter profiles |
| P1 | MCP/Tool Provider Interface 부재 | Jira/Datadog/Sonar/Sentry 추가 시 Core workflow 변경 위험 | Capability Provider Contract |
| P1 | Stage Handoff가 모든 단계에 self-contained하지 않음 | Agent 교체 시 이전 대화 추론 필요 | `stage-input-pack.yaml` 표준화 |
| P2 | 한글 View와 내부 key의 Data Dictionary 부족 | BA가 `truth`, `validity`, `authority` 의미를 매번 학습 | 공통 Column/Field Dictionary |
| P2 | `design/experiments`/`validation`이 현재 사용자 동선과 함께 노출 | 신규 사용자가 Candidate를 Current Contract로 오인 | README에서 Current/Reference/Archive 경계 강화 |

---

# D. 제거/병합/단순화 제안

| Artifact | 현재 역할 | 판정 | 이유 | 대체/개선 |
|---|---|---|---|---|
| Business Source Catalog | 입력 문서 Catalog | KEEP | Provenance 핵심 | Project-level 1개, RQ별 생성 금지 |
| Glossary | 용어 통일 | KEEP | 다수 RQ 재사용 | Project-level |
| 6W Business Definition | 업무 의미 구조화 | MERGE | Requirement Analysis/Customer Spec과 중복 | Standard에서는 요구분석 Section, Enterprise만 별도 View |
| Requirement Analysis | FR/BR/AC/질문 | KEEP | 핵심 분석 계약 | RQ Boundary Card 포함 |
| Customer Functional Specification | 고객 검토 | KEEP | 고객 합의 필요 | Canonical에서 generate, 직접 중복 입력 금지 |
| Process Analysis | AS-IS/TO-BE | OPTIONAL | 모든 CRUD RQ에 불필요 | Process-heavy만 활성화 |
| Impact Analysis | 영향 분석 | KEEP | Brownfield 핵심 | Lite Greenfield에는 조건부 |
| Functional Design | 목표 동작 | MERGE | Blueprint와 경계 혼동 | `Engineering Design` 상위 Section으로 통합 검토 |
| Development Blueprint | 상세 개발 준비 | MERGE/SIMPLIFY | Functional Design + PGM Spec과 반복 | Engineering Design + PGM delta 구조 |
| PGM Spec | 프로그램 상세 | OPTIONAL | L0/L1에 과도 | L2 이상만 Full Spec |
| Data/Query Spec | 데이터 상세 | OPTIONAL | Data-heavy에서만 필요 | Engineering Design Section 또는 별도 조건부 |
| Interface Spec | 연계 상세 | OPTIONAL | Interface RQ에서만 필요 | Engineering Design Section 또는 별도 조건부 |
| Test Scenario | AC→TC | KEEP | Verify 핵심 | structured table 유지 |
| Implementation Result | 실제 변경 | KEEP | Reverse Sync/Knowledge 근거 | 자동 Source Diff summary 포함 |
| Verification Result | 최종 검증 | KEEP | 고객/QA/PM 핵심 | Acceptance Sheet 역할 통합 가능 |
| PM Worklist | 진행 추적 | KEEP | 공통 사용자 View | MD/XLSX 생성 View |
| Source Analysis Result | 기술 Evidence | INTERNAL_ONLY | 고객/PM이 직접 볼 필요 없음 | Stage Input Pack에 필요한 부분만 전달 |
| Evidence Envelope/Stage Evidence | Runtime evidence | INTERNAL_ONLY | Enterprise guard에는 유효 | Standard/Lite에서 사용자 노출 금지 |
| Action Permission/Target Write Proof | 실행 안전 | OPTIONAL/INTERNAL_ONLY | 모든 프로젝트에 강제하면 과대설계 | Enterprise 또는 risky write에만 |
| Work Unit/PGM Write Lane | Recovery/Write orchestration | OPTIONAL/INTERNAL_ONLY | Small project에는 과함 | Enterprise parallel/recovery profile |

## RQ 1건 기준 현재 부담 추정

Starter Matrix 기본값대로라면 Project-level 산출물을 제외해도 일반 RQ가 읽거나 생성/갱신해야 하는 주요 Artifact가 약 10~12개까지 증가할 수 있다.

이해해야 하는 대표 ID:
- Source/Legacy Requirement ID
- RQ
- FR
- BR
- AC
- PGM
- TASK
- TC
- CR/ALT/ASM (상황별)

이 자체는 Canonical 내부에서는 타당하지만 사용자가 전부 직접 관리해서는 안 된다.

## 권장 Profile

### Lite

사용자가 주로 보는 것:
1. Requirement/Customer View
2. Engineering Design(필요 Section만)
3. Test/Verification
4. Worklist

Internal:
- Canonical IDs/Trace
- Source Analysis
- Stage Input Pack

비활성 기본값:
- 별도 6W 문서
- 별도 Process 문서
- Full PGM Spec
- Action Permission/Recovery lane
- Knowledge Promotion workflow UI

### Standard

추가:
- Impact Analysis
- Process Analysis 조건부
- PGM Spec L2 조건부
- Knowledge Promotion
- Change/STALE

### Enterprise

추가:
- Evidence Envelope
- Action Permission
- Target Write Proof
- Work Unit/Recovery
- Semantic Merge/Branch Delta
- Advanced Telemetry/Cost
- Mandatory deterministic validators

---

# E. 빠진 설계

현재 문서 어디에도 실행 계약으로 충분히 정의되지 않은 항목만 기록한다.

1. **Legacy Requirement → Canonical RQ Boundary Normalization Contract**
   - 기존 ID를 RQ로 그대로 승격할지 Source Requirement로 보존할지
   - 동일 업무목표의 다수 Row를 RQ/FR로 묶는 기준
   - Split/Merge 시 원본 ID trace
2. **Artifact Profile Contract**
   - Lite/Standard/Enterprise 별 required/optional/internal-only
3. **Capability Provider Interface**
   - Source Provider
   - Business Document Provider
   - Issue/PM Provider
   - Test Provider
   - Monitoring Provider
   - Deployment Provider
   - Notification Provider
4. **Source Diff Reverse Sync Contract**
   - changed symbol/sql/table → PGM → FR/BR/AC candidate
   - semantic change classification
5. **Low-Agent Skill Procedure Contract**
   - Precondition / Decision / Stop / Escalation / Quality Check
6. **Stage Input Pack 공통 Schema**
7. **Field/Data Dictionary Contract**
   - 한글명, key, 설명, source, 없을 경우, example, required/conditional
8. **Deterministic Validation Registry**
   - ID/Revision/Trace/Required/Open preservation/status transition

---

# F. Persona Walkthrough 결과

| Persona | 첫 진입점 | 읽는 문서 | 작성/검토 문서 | 어려운 점 | 개선 |
|---|---|---|---|---|---|
| Customer | Customer Functional Spec | 고객 기능정의서 | 결정/OPEN 확인 | 어떤 항목이 확정/추론/미확정인지 입력 Guide 약함 | 고객 View 상태값을 한글화하고 generated view로 제공 |
| BA | `sdlc/README` + Requirement | Source/6W/요구분석 | RQ/FR/BR/AC | Legacy Row→RQ Boundary가 암묵적 | Boundary checklist/decision table |
| Designer | 요구분석/영향/설계 | 여러 MD + Source result | Engineering Design | Functional Design vs Blueprint 역할 중복 | Engineering Design 통합 |
| Developer | PGM/TASK | PGM Spec/Blueprint/Context | Source/Implementation Result | Full Spec이 작은 수정에도 과함 | L0/L1/L2 spec level 적용 |
| QA | AC/TC | Requirement/Test | Test/Verification | AC 품질이 Agent마다 달라질 수 있음 | AC schema + validator |
| PM | `전체작업목록` | Worklist | 담당/일정 Optional | 아직 실제 Worklist가 빈 skeleton | Pilot 자동 생성 예시 필요 |

## “처음 Repository를 열었을 때 무엇부터?”

`sdlc/README.md`는 비교적 명확하다. 하지만 Root에서 `sdlc/design/experiments`, `validation`, Starter, Baseline이 모두 존재하므로 신규 사용자가 “현재 작성해야 할 문서”와 “과거 설계 검증 자료”를 구분하려면 Repository map이 더 명시적이어야 한다.

---

# G. Greenfield vs Brownfield 결과

| 영역 | Greenfield | Brownfield | 개선 필요 |
|---|---|---|---|
| 업무분석 | 8/10 | 8/10 | 공통 6W/RQ/FR/BR/AC는 양쪽 사용 가능 |
| 설계 | 7/10 | 8/10 | 신규 Architecture/API/Data 설계용 template/profile 보강 |
| Source 준비 | 5/10 | 9/10 | Starter의 Source Profile이 Brownfield stack에 고정 |
| 개발 | 7/10 | 8/10 | Greenfield는 package/module 생성 rule 필요 |
| Test | 8/10 | 8/10 | 공통 AC→TC 구조 사용 가능 |
| Change | 6/10 | 6/10 | Source Diff reverse path 공통 부족 |

### Greenfield 핵심 문제
- `project-onboarding.yaml` 기본 `mode: BROWNFIELD`
- `source_profile`이 Java/Spring/JSP/MyBatis/Oracle 전제
- `greenfield-default.yaml`은 workflow/file naming 중심이고 architecture/data/API creation contract가 얕다.

### Brownfield 핵심 강점
- Existing Asset Bootstrap
- JSP→Controller→Service→Mapper→Procedure/Table 탐색
- Dynamic SQL/Procedure blind spot 인식
- Source Evidence ≠ Business Truth 원칙

---

# H. Customization Matrix

| 항목 | Config | Skill | Adapter | Core 개발 | 현재 지원 |
|---|---|---|---|---|---|
| 프로젝트명/모드/언어 | O | - | - | - | O |
| Stage 표시/사용 여부 | O(선언) | - | - | - | 개념 O, 실제 schema 보강 필요 |
| Artifact 선택 | O | - | - | - | O, Profile 없음 |
| 한글 명칭/Worklist 컬럼 | O | - | - | - | O |
| 고객 Excel Column Mapping | O + Mapping | O | 파일 Reader | - | 부족 |
| Word/PPT/PDF Extraction | Mapping | O | Parser/Connector | - | Skill hint만 있음 |
| Spring Boot/JPA/PostgreSQL | Profile | O | Source Analyzer | - | Starter template 수정 필요 |
| React/Kotlin/Kafka | Profile | O | Source/Build/Trace Adapter | - | 미정의 |
| Jira 요구사항 | Mapping | O | Issue Provider | - | 미정의 |
| Confluence/Slack | Mapping | O | Document/Notification Provider | - | 미정의 |
| Sonar/Sentry/Datadog/Grafana | Policy | - | Monitoring/Test Provider | - | 미정의 |
| 신규 Stage | O | O | 필요시 | Contract 변경 시 | 개념만 있음 |
| 신규 Entity/Relation | 일부 | O | - | O | Canonical migration 필요 |
| 고객사 용어 변경 | O | - | - | - | O |

## Configuration vs Custom Development Boundary

권장 경계:

```text
명칭/필수여부/순서/경로/컬럼/정책
→ Config

문서에서 무엇을 추출하고 어떻게 판단할지
→ Skill

외부 시스템/도구와 연결하고 데이터를 표준 Event/Evidence로 변환
→ Adapter/Provider

새로운 SDLC 의미(Entity/Relation/State/Guard semantics)
→ Core
```

---

# I. Artifact Chain Traceability 결과

| Origin | 다음 산출물 | 연결 Key | 자동 연결 가능 | 정보 손실/위험 |
|---|---|---|---|---|
| Raw Excel Row | Source Requirement | Legacy Requirement ID | O | 현재 공식 entity가 불명확 |
| Source Requirement | 6W | source_id/locator | O | Why/Actor 등 없는 경우 OPEN 유지 필요 |
| 6W | RQ | scenario/source IDs | 부분 | RQ split/merge 규칙 없음 |
| RQ | FR | rq_id | O | FR boundary 품질은 reasoning 의존 |
| FR | BR/AC | fr_id | O | BR truth state/AC completeness drift |
| RQ/FR/BR/AC | Customer Spec | IDs | O | 사람이 복사하면 중복/Revision drift |
| Process | Functional/Engineering Design | PROC/FR | O | 별도 문서 간 수동 복사 위험 |
| Source Analysis | Impact | ART/PGM/DATA + evidence | O | current schema에 formal handoff 부족 |
| Impact | Engineering Design | impact candidate IDs | O | candidate/confirmed 상태 유지 필요 |
| Engineering Design | PGM/TASK | PGM/FR/AC | O | Blueprint/PGM Spec 중복 |
| TASK/PGM | Source Change | TASK/PGM/ART | O | target revision guard 필요 |
| Source | Implementation Result | commit/file/symbol | O | reverse semantic classification 부족 |
| AC | TC/Test | AC ID | O | deterministic coverage 가능 |
| Source Diff | FR/BR/AC | PGM→relation | 부분 | 현재 가장 큰 끊김 |

## Bidirectional Traceability

- Document → Source: **7/10**
- Source → Document: **4/10**

---

# J. Recommended SDLC Artifact Architecture vNext

목표:

```text
사용자가 읽는 문서는 최소화
+ 내부 Traceability는 구조화
+ Agent는 Stage Input Pack만 사용
```

## Level 1 — 고객/PM View

1. `전체작업목록.md/.xlsx`
2. `RQ-xxxx_업무명_요구사항-고객검토.md`
   - Requirement + 6W + Scope + AS-IS/TO-BE + Rule/Exception + Decision/Open + AC
3. `RQ-xxxx_업무명_검증결과.md`
   - Acceptance/결과/남은 Open

고객이 별도의 6W, Requirement Analysis, Customer Spec을 모두 읽지 않게 한다.

## Level 2 — Engineering View

1. `RQ-xxxx_업무명_엔지니어링설계.md`
   - Process(조건부)
   - Impact
   - Functional Behavior
   - UI/API/Batch/Event
   - Data/Transaction/Auth
   - PGM Candidate
2. `PGM-xxxx_업무명_프로그램설계.md`
   - L2 이상만 Full Spec
3. `RQ-xxxx_업무명_테스트검증.md`
   - AC→TC→Result
4. `RQ-xxxx_업무명_구현결과.md`
   - Source Diff + semantic change summary

## Level 3 — Harness Internal

- Canonical Entity/Relation
- Business Source Manifest/Locator
- Source Analysis Result
- Evidence/Truth
- Stage Input Pack
- Alerts/Assumptions
- Change/STALE graph
- Target Write Proof/Action Permission (profile-based)
- Work Unit/Recovery (Enterprise only)

## 핵심 원칙

Human Artifact와 Agent Handoff를 분리한다.

```text
Human-readable MD
+
Structured Stage Input Pack
→ Agent
```

Sidecar를 모든 문서마다 만드는 대신 **Stage Input Pack 1개**를 runtime/generated 형태로 생성하는 것을 우선한다.

---

# J-1. Simplified Profile 제안

| Capability/Artifact | Lite | Standard | Enterprise |
|---|---|---|---|
| Worklist | MUST | MUST | MUST |
| Customer Requirement View | MUST | MUST | MUST |
| 별도 6W 문서 | OFF | OPTIONAL | OPTIONAL |
| Process Analysis | CONDITIONAL | CONDITIONAL | MUST for process-heavy |
| Impact | CONDITIONAL | MUST | MUST |
| Engineering Design | MUST | MUST | MUST |
| Full PGM Spec | L2 only | L2 only | L1/L2 configurable |
| Test/Verify | MUST | MUST | MUST |
| Source Analysis | Internal | Internal | Internal |
| Knowledge Promotion | OFF/Light | ON | ON |
| STALE propagation | Direct only | ON | ON |
| Action Permission | OFF | Risky action only | ON |
| Work Unit/Recovery | OFF | OFF/Optional | ON |
| Semantic Merge | OFF | Optional | ON |
| Advanced Telemetry | OFF | Basic | ON |

---

# J-2. MCP / Tool 확장 권장 구조

```text
Core SDLC
  ↓
Capability Interface
  ├─ BusinessDocumentProvider
  ├─ SourceProvider
  ├─ IssuePmProvider
  ├─ TestProvider
  ├─ MonitoringProvider
  ├─ DeploymentProvider
  └─ NotificationProvider
```

Provider output은 최소 다음 표준 객체로 normalize한다.

- Evidence
- ExternalEvent
- ActionResult
- ArtifactLocator
- Health/Availability

Tool 장애 시:
- Provider 상태 `UNAVAILABLE`
- 해당 Evidence/Action만 Defer
- Core workflow 전체는 계속

---

# J-3. Source → Documentation Reverse Sync 권장 구조

```text
Source Diff
→ Changed File/Symbol/SQL/Table/Procedure
→ PGM/ART/DATA Mapping
→ Semantic Change Classification
→ FR/BR/AC/Design 영향 Candidate
→ STALE Candidate
→ Human/L2 Review
→ Revision
```

분류:

- `NO_BUSINESS_CHANGE`
- `TECHNICAL_CHANGE`
- `BEHAVIOR_CHANGE`
- `BUSINESS_RULE_CHANGE`
- `UNKNOWN`

결정론적으로 가능한 부분:
- changed file/symbol/table 탐지
- PGM relation traversal
- source hash/revision
- candidate stale marking

Agent 판단이 필요한 부분:
- business semantics changed 여부

---

# 10. Low-capability Agent Readiness 상세

## 10.1 Stage별 L1 실행 평가 (1~5)

| Stage | 입력 명확 | Step 명확 | Output Schema | Example | 추론 의존도(5=높음) | L1 성공 가능 |
|---|---:|---:|---:|---:|---:|---:|
| Onboarding | 4 | 3 | 4 | 3 | 2 | 3 |
| Business Source Extraction | 4 | 3 | 3 | 2 | 3 | 3 |
| 6W Business Definition | 3 | 3 | 4 | 3 | 3 | 3 |
| RQ Boundary | 2 | 2 | 2 | 2 | 5 | 1 |
| FR / BR / AC | 3 | 3 | 3 | 3 | 4 | 2 |
| Customer Functional Spec | 3 | 2 | 3 | 2 | 4 | 2 |
| Process Analysis | 3 | 2 | 2 | 2 | 4 | 2 |
| Source Discovery | 4 | 3 | 4 | 2 | 5 | 2 |
| Impact Analysis | 3 | 2 | 3 | 2 | 5 | 2 |
| Functional/Engineering Design | 3 | 3 | 4 | 2 | 4 | 3 |
| Development Blueprint | 4 | 3 | 5 | 2 | 4 | 3 |
| PGM / TASK | 3 | 2 | 3 | 2 | 4 | 2 |
| Source Change | 4 | 3 | 3 | 2 | 5 | 2 |
| Test Scenario | 4 | 3 | 4 | 3 | 2 | 4 |
| Verify | 4 | 3 | 3 | 3 | 3 | 3 |
| Change / STALE | 2 | 2 | 2 | 2 | 5 | 1 |

## 10.2 Skill Procedure 평가

| Skill | Procedure 명확성 | Decision Rule | Stop Rule | Output Schema | L1 적합성 |
|---|---:|---:|---:|---:|---:|
| Brownfield Source Analysis | 3/5 | 2/5 | 1/5 | 4/5 | 2/5 |
| SoP Business Extraction | 3/5 | 2/5 | 1/5 | 3/5 | 2/5 |
| Source Change | 3/5 | 2/5 | 2/5 | 2/5 | 2/5 |

공통 누락:
- Precondition
- Evidence acceptance rule
- Stop condition
- Escalation target
- Output field-level rule
- Quality check checklist

## 10.3 Artifact 자유서술 분류

| Artifact | 분류 | 판단 |
|---|---|---|
| Business Definition | SEMI_STRUCTURED | 6W 표는 구조적이나 Candidate/Scope는 자유서술 |
| Customer Functional Spec | FREE_FORM~SEMI | Section만 있고 필드 계약 약함 |
| Development Blueprint | STRUCTURED | 현재 가장 L1 친화적 |
| Source Analysis Result | STRUCTURED | Schema는 좋으나 작성 Procedure 부족 |
| Process Analysis | SEMI/FREE | Current Starter의 전용 강한 schema 부족 |
| Impact Analysis | SEMI | 차원 checklist를 강화해야 함 |

## 10.4 Context Window 의존성

| Stage | 필요한 문서 수 | 평가 | Context Pack 필요 |
|---|---:|---|---|
| Intake | 1~3 | GOOD | 선택 |
| 6W/RQ | 3~6 | REVIEW | 권장 |
| Impact | 5~10+ | HIGH | MUST |
| Design | 5~9 | HIGH | MUST |
| Development | 5~10+ + Source | HIGH | MUST |
| Test | 3~6 | REVIEW | 권장 |
| Change | 관계에 따라 8+ | HIGH | MUST |

Baseline에는 Development Context Pack 개념이 있으나 **모든 Stage 공통 self-contained input contract**가 필요하다.

## 10.5 Agent Replaceability

**Agent Replaceability Score: 5/10**

Canonical ID/Status 개념은 교체 가능성을 돕지만, 실제 Starter artifact가 모든 reasoning 결과/decision/evidence를 충분히 handoff하지 않는다.

현재 판정:

**STANDARD_AGENT_REQUIRED**

하위 점수:

| 하위 항목 | 점수 |
|---|---:|
| 단계별 입력 명확성 | 6/10 |
| Skill Procedure 명확성 | 4/10 |
| Output Template 구조화 | 6/10 |
| Context 최소화 | 6/10 |
| Agent 교체 가능성 | 5/10 |
| Escalation 안전성 | 4/10 |
| Model 간 결과 안정성 | 4/10 |
| Deterministic Validation | 4/10 |

---

# 11. Pilot — 근태마감 End-to-End 재검증

## 11.1 Pilot Source

`요구사항목록.xlsx`의 근태마감 영역에는 다음과 같은 기존 Requirement Row가 있다.

- REQ_TM_TE016 월근태확인 조회
- REQ_TM_TE017 일근태입력/마감 조회
- REQ_TM_TE018 일근태입력/마감 신청 등록
- REQ_TM_TE019 일근태입력/마감 신청 수정
- REQ_TM_TE020 일근태입력/마감 신청 삭제
- REQ_TM_TE021 일근태입력/마감 강제마감 수정
- REQ_TM_TE022~024 전자결재 조회/송신/수신
- REQ_TM_TE025~031 월마감/메일/전자결재 관련 기능

공통 상위 설명은 `10분단위 근무계획 개선 근태마감 반영을 구현`이다.

## 11.2 가장 중요한 Boundary 문제

현재 입력만 보고 가능한 해석이 최소 3개다.

A. Excel의 각 `REQ_TM_TE0xx`를 Canonical RQ로 유지
B. `근태마감`을 1개 RQ로 만들고 기존 Row를 FR로 변환
C. 일마감 / 월마감 / 전자결재를 복수 RQ로 재그룹화

현재 Starter의 `RQ는 독립적인 Business Change Outcome인가?` 질문만으로 L1 Agent가 이를 안정적으로 결정할 수 없다.

권장:
- 원본 `REQ_TM_TE017`은 `source_requirement_id`로 무조건 보존
- Canonical RQ는 별도 UID/Display ID
- 자동 grouping은 Candidate만 생성
- group/split confidence가 낮으면 `BOUNDARY_AMBIGUOUS`
- L2/Human이 결정

## 11.3 focal item: REQ_TM_TE017

원본에서 확정 가능한 것:
- 업무구분: 근태관리
- Level2: 근태마감
- Source Requirement ID: REQ_TM_TE017
- 상위 목적문구: 10분단위 근무계획 개선 근태마감 반영
- 작업: 일근태입력/마감 조회

원본만으로 확정 불가능:
- Who
- When
- Where
- 상세 Why
- 조회조건/필드
- 권한
- AS-IS/TO-BE 차이
- Validation/Exception
- Data/Table
- Program/Source
- AC/Test expectation

따라서 올바른 Low-Agent 결과는 OPEN을 많이 남기는 것이다. “일근태 담당자가 마감일에 ESS 화면에서 조회한다” 같은 문장을 창작하면 실패다.

## 11.4 Persona별 막힘

- Customer: Customer Spec의 대부분이 OPEN. 질문 우선순위가 필요.
- BA: RQ grouping/split 결정을 못 함.
- Designer: Source/DB 자료 없이는 Impact 확정 불가.
- Developer: PGM/Source Target 없음.
- QA: AC가 없어 Test Scenario 생성 품질 낮음.
- PM: 기존 16개 Legacy ID와 새 RQ/FR 계층이 어떻게 연결되는지 필요.
- Change Manager: 구현 후 Source Diff가 어느 원본 Row/BR/AC에 영향을 주는지 reverse contract 없음.

---

# K. 개선 Roadmap

## P0 — 고객 Pilot 전에 반드시

1. `Legacy Requirement → Canonical RQ Boundary` 계약
2. Lite/Standard/Enterprise Artifact Profile
3. `Stage Input Pack` 공통 Schema
4. Low-Agent Skill Procedure / Stop / Escalation Contract
5. Source Diff Reverse Sync semantic classification
6. Required/ID/Trace/OPEN preservation deterministic validator 설계

## P1 — 첫 프로젝트 Pilot 중

1. Starter mode 기본값 `AUTO`
2. Brownfield-specific source profile을 stack-neutral core + adapter example로 분리
3. Customer Spec/Requirement Analysis의 필드 Dictionary 추가
4. Engineering Design 통합 실험
5. Provider Interface로 Jira/Test/Monitoring 중 1개 연결 PoC
6. Worklist에 실제 Pilot RQ/FR/PGM/TASK sample 생성

## P2 — Enterprise 확장 시

1. Action Permission / Target Write Proof profile gating
2. Work Unit / Recovery / Write Lane
3. Semantic Merge/Branch Delta 자동화
4. Advanced Telemetry/Cost/Adoption
5. Provider health/retry/degraded-mode standard

---

# Before / After 요약

## Before

```text
Starter 13-step
+ 15 Artifact Matrix(13 default required)
+ Brownfield-specific Source Profile
+ Skill은 설명/순서 중심
+ Context Pack은 주로 Development 중심
+ Source→Doc Reverse Sync 불완전
```

## Recommended After

```text
Project Profile(Lite/Standard/Enterprise)
→ Requirement/Customer View
→ Engineering Design
→ PGM Spec only when complex
→ Source/Test/Verification

각 Stage는
Stage Input Pack
+ Procedure Skill
+ Deterministic Validator
+ Escalation
로 실행
```

---

# 최종 질문 1

> 이 Harness를 처음 보는 고객사 BA 1명, 개발자 1명, PM 1명에게 오늘 전달한다면, 별도 교육 없이 Starter Pack과 산출물만으로 첫 RQ Pilot을 수행할 수 있는가?

## NO, TRAINING REQUIRED

가장 큰 이유 3가지:
1. Legacy Requirement Row를 RQ/FR로 어떻게 정규화하는지 결정 규칙이 부족하다.
2. Starter 기본 Artifact 수와 Brownfield 설정이 많아 “무엇을 꼭 작성해야 하는지”가 첫 사용자의 판단에 맡겨진다.
3. OPEN/Truth/Source Evidence 개념은 있으나 필드별 작성 Guide와 예제가 충분하지 않아 BA/Dev가 동일 품질로 채우기 어렵다.

# 최종 질문 2

> 각 Stage를 서로 다른 저수준 Agent에게 하나씩 맡기고 이전 대화 History 없이 Artifact와 Stage Input Pack만 전달했을 때 End-to-End Workflow가 유지될 수 있는가?

## NO, STANDARD AGENT REQUIRED

| 위험 Stage | 실패 이유 | 필요한 개선 |
|---|---|---|
| RQ Boundary | Legacy Row grouping/split이 암묵적 업무 추론 | Boundary Decision Rule + escalation |
| Impact / Source Discovery | 탐색 종료/증거 채택/Blind spot 판정 규칙 부족 | Search Checklist + Stop Rule + Evidence schema |
| Change / Reverse Sync | Source Diff에서 업무 의미 변경 분류 계약 부재 | Semantic Change Classifier + STALE traversal |

---

# DECISION_REQUIRED

본 Review는 개선안을 제안하지만 `SDLC_DESIGN_SESSION_SECOND/base`에는 병합하지 않는다.

다음 Prototype을 별도 실험 폴더에 최소 변경으로 추가해 효과를 비교한다.

1. Artifact Profile (`Lite / Standard / Enterprise`)
2. Stage Input Pack 공통 Template
3. Low-Agent Skill Procedure Contract
4. Source Diff Reverse Sync Contract
5. `REQ_TM_TE017` Pilot Handoff Example

최종 채택 여부는 사용자 비교 검증 후 결정한다.
