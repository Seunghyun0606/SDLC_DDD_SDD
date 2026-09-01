# Candidate B+ — Source-ready Execution / Customer 6W View / Business SoP Evidence Extraction

> 상태: `EXPERIMENT / NOT BASELINE`
> Parent: Candidate B validation line
> Candidate A와 결합하지 않는다.

## Quick Start

이 Branch는 4개 질문을 Candidate B 방식으로 검증한다.

1. 6W 업무정의에 Truth/Evidence를 유지하면서 Stage 진행과 실행권한을 분리할 수 있는가?
2. 화면/CRUD/Logic/Integration/Query/Data/Code까지 포함한 상세 Development Evidence Blueprint가 있는가?
3. 고객 문서에 6W와 합의상태를 보여주되 내부 Work Unit/Target Proof 복잡성은 숨길 수 있는가?
4. PPT/XLSX/Word/PDF를 Evidence-aware Extraction Skill로 처리하고 BR/K1 승격을 안전하게 분리할 수 있는가?

## Design Flow

```text
Customer/Legacy SoP
→ Format-aware Evidence Extraction Skill
→ 6W Business Evidence
→ RQ / FR / BR Candidate
→ Customer Decision & Acceptance View
→ Engineering Design
→ Development Evidence Blueprint
→ Development Evidence Pack (Manifest)
→ Current Source Evidence
→ Target Write Proof
→ Work Unit / PGM Lane
→ Draft Source Write
→ Executed Test / Verify
→ Knowledge Promotion Eligibility
```

## 1. 6W + Evidence

각 Who/When/Where/What/How/Why에:

- value
- truth
- evidence locator
- revision

을 유지한다.

상세: `04_sixw_business_definition_and_evidence_blueprint.md`.

## 2. Development Evidence Blueprint

`development-evidence-pack.yaml`은 상세명세가 아닌 Evidence/Artifact Manifest다.

실제 Blueprint는:

- 6W
- UI/Field
- CRUD
- Business Logic
- State/Error
- Integration
- Query/Data
- Common Code
- Transaction/Auth/Audit
- Current Source Mapping
- Test
- Blind Spot
- Target Write Proof
- Action Permission

을 포함한다.

Template: `templates/development-evidence-blueprint.md`
Sample: `sample/RQ-PILOT-017_development-evidence-blueprint.md`.

## 3. Customer 6W View

고객에게는 내부 `progress`, Work Unit, PGM Lane을 기본 노출하지 않고:

- 6W 업무정의
- 합의상태
- AS-IS/TO-BE
- Rule/Exception
- 고객 접점
- 완료조건
- 검증/배포 상태

를 보여준다.

Sample: `sample/RQ-PILOT-017_customer-decision-acceptance-view.md`.

## 4. Template-driven SoP Evidence Extraction

Business Evidence Card를 Primary Input으로 두지 않는다.

```text
Original PPT/XLSX/Word/PDF
+ Source Metadata
→ skills/sop-business-extraction/SKILL.md
→ templates/sop-evidence-extraction-output.yaml
→ 6W + Candidate Evidence
→ Authority/Scope/Effective Review
→ BR Confirm Candidate
→ High-blast Human Confirmation
→ K1 Eligibility
```

Card는 Derived Review/Audit View로 유지한다.

상세: `05_template_driven_sop_evidence_extraction_contract.md`.

## User Example

`sample/ESS-FLEX-001_business-definition-6w-evidence.md`에 탄력근로제 ESS 예시와 Source Write를 막는 Evidence Gap을 함께 기록했다.

## Permission Principle

문서가 상세해도 다음이 OPEN이면 실제 고객 Source Write/merge/release를 제한할 수 있다.

- Role/Profile
- 실제 Entry/Menu
- Code Master
- Schema/Key/Index
- Runtime Lock/Performance
- Current Source Revision
- Executed Test

## DECISION_REQUIRED

1. 6W의 OPEN이 어떤 Action만 제한해야 하는가?
2. Development Evidence Blueprint를 Source Write 필수입력으로 할지
3. 고객 6W의 합의상태 단계를 얼마나 단순화할지
4. 고객별 SoP Extraction Overlay 작성 범위
5. Low-risk BR 자동 Confirm 후보 기준과 High-blast K1 Human Guard
