# Candidate A+ — Source-ready / Customer Communication / Business SoP Extraction

> 상태: `EXPERIMENT / NOT BASELINE`
> Parent: Candidate A validation line
> Candidate B와 결합하지 않는다.

## Quick Start

이 Branch는 다음 4개 질문을 검증한다.

1. 업무정의서가 6W(Who/When/Where/What/How/Why)로 충분히 업무맥락을 설명하는가?
2. 개발자가 화면/CRUD/Logic/Integration/Query/Data/Code까지 이해할 수 있는 상세 Blueprint가 있는가?
3. 고객 Communication 문서에 6W를 포함하면서 기술복잡도는 숨길 수 있는가?
4. 비정형 PPT/XLSX/Word/PDF를 Card-first가 아니라 Template-driven Skill로 추출할 수 있는가?

## Design Flow

```text
Customer/Legacy Source
→ Format-aware SoP Extraction Skill
→ 6W Business Definition Candidate
→ RQ / FR / BR / AC
→ Customer Functional Specification
→ Functional / Program Design
→ Development Blueprint
→ Development Context Pack (Manifest)
→ Current Brownfield Source
→ Source Change
→ Test / Verify
```

## 1. 6W Business Definition

각 핵심 업무 Scenario는 다음을 가진다.

- Who: Role/Profile/System Actor
- When: Trigger/Frequency/State
- Where: Channel/Menu/Screen/Batch/API
- What: Object/Input/Output/Field
- How: CRUD/Validation/State/Exception/Integration
- Why: Goal/Policy/Pain Point

상세 계약: `04_sixw_business_definition_and_development_blueprint.md`.

## 2. Development Blueprint

`development-context-pack.yaml`은 상세설계가 아니라 Manifest다.

실제 개발 입력은 최소:

```text
6W
+ Screen/Field
+ CRUD
+ Core Logic
+ State/Validation/Error
+ Integration
+ Query/Data
+ Common Code
+ Transaction/Auth/Audit
+ Brownfield Source Mapping
+ Test Mapping
```

을 포함한다.

Template: `templates/development-blueprint.md`
Sample: `sample/RQ-PILOT-017_development-blueprint.md`

## 3. Customer View

고객 문서에는 6W를 업무언어로 Projection한다.

- 6W 업무문장
- AS-IS/TO-BE
- Process
- Rule/Exception
- 고객 접점
- 완료조건
- 고객 확인 필요사항

Sample: `sample/RQ-PILOT-017_customer-functional-spec.md`.

## 4. Template-driven SoP Extraction

`Business Source Card`를 고객의 Primary Input으로 쓰지 않는다.

```text
Original PPT/XLSX/Word/PDF
+ 최소 Source Metadata
→ skills/sop-business-extraction/SKILL.md
→ templates/sop-extraction-output.yaml
→ 6W/RQ/FR/BR/UI/Data/Integration Candidate
→ Human Review
→ Canonical
```

기존 Card는 Derived Review/Audit View로 유지한다.

상세: `05_template_driven_sop_extraction_contract.md`.

## User Example Sample

`sample/ESS-FLEX-001_business-definition-6w.md`에는 사용자가 제시한 탄력근로제 ESS 예시를 6W로 구조화하고, 개발 전에 추가로 확인해야 할 UI/CRUD/Rule/Integration/Data 질문을 연결했다.

## Source-ready Gate

CRITICAL OPEN이면 해당 Source 영역 Write 전에 해결한다.

- Role/Profile
- UI/Field
- CRUD
- Rule/Exception
- Integration
- Query/Table/Key
- Common Code
- Transaction/Auth/Error
- Current Source Mapping
- Test/AC

## DECISION_REQUIRED

1. 6W를 모든 RQ가 아니라 핵심 Scenario별 필수로 둘지
2. Development Blueprint를 Development Stage 필수 Artifact로 승격할지
3. Customer Functional Specification의 6W를 고객 승인 항목으로 둘지
4. SoP Extraction Skill의 고객별 Overlay 작성 수준
5. Business Source Card를 내부 Derived Artifact로 한정할지
