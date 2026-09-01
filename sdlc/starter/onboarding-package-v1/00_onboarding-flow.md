# 00. Onboarding Flow

## Phase 1 — Intake
고객 제공:
- Project 기본정보
- Business Source 원본
- Manifest
- Glossary
- Artifact Selection
- Source Profile
- Repository/Snapshot

Harness 생성:
- Source Catalog
- Format별 Extraction Queue
- OPEN 목록
- 초기 Project Overlay

## Phase 2 — Business Analysis

```text
Raw Document
→ Evidence Fragment
→ 6W Business Scenario
→ RQ Candidate
→ FR Candidate
→ BR Candidate
→ AC Candidate
```

Gate:
- RQ는 독립적인 Business Change Outcome인가?
- 주요 Scenario의 Who/When/Where/What/How/Why가 있는가?
- OPEN과 INFERRED가 구분되어 있는가?

## Phase 3 — Customer Communication
- Customer Functional Specification
- AS-IS/TO-BE
- 업무 Process
- 화면/항목 정의
- Rule/Exception
- Acceptance Criteria
- 고객 결정사항

## Phase 4 — Brownfield Discovery

```text
RQ/FR/BR
→ Entry Point
→ JSP/Controller/Service
→ Mapper Interface
→ Mapper XML
→ Procedure/SQL
→ Table/Code
→ Downstream/Batch/Interface
```

Source의 현재 동작은 `OBSERVED`, 업무 의미는 별도 판단한다.

## Phase 5 — Skillization
반복되는 패턴만 Skill Candidate로 만든다.
- MyBatis Mapper 찾기
- 공통코드 조회 패턴
- Service Transaction Pattern
- Legacy Error 처리
- 고객별 XLSX/PPT SoP extraction mapping

1회성 업무정책은 Skill로 만들지 않는다.

## Phase 6 — Development Blueprint
필수:
- 6W
- Screen/Field
- CRUD
- Core Business Logic
- State/Validation/Error
- Integration
- Query/Data
- Common Code
- Transaction/Auth/Audit
- Brownfield Source Mapping
- Test Mapping
- OPEN/Blind Spot

## Phase 7 — Source Proposal / Implementation
Default: `PROPOSAL_ONLY`

Actual Write 전:
- 실제 target file/symbol
- current revision/hash
- actual common code
- DB key/index/lock
- security/profile
- integration target
- test/build command
- rollback/recovery approach

## Phase 8 — Verify
- RQ → FR → BR → PGM → TASK → AC/TC Trace
- 실행 Test Evidence
- 변경되지 않아야 할 기존 기능
- OPEN/Assumption 잔여
- 고객 확인사항
- Source/문서 revision 정합성
