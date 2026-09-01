# Program Reference

## Purpose
기존 Program 재사용을 우선하고 실제 Artifact/Symbol 근거 없이 PGM/테이블을 발명하지 않는다. Program Spec은 단순 역할 설명이 아니라 **Production Source 구현 전 Definition of Ready**를 판정할 수 있는 수준으로 작성한다.

## Required Input
- Stage: `PROGRAM`
- Functional Design + Impact
- Source Evidence 또는 `OPEN_REAL_SOURCE`
- Project Architecture / Coding / DB / Test Standard
- 관련 AC/TC Candidate

## Optional Input
- Existing Program Summary
- API/Batch/Interface Contract
- Data Dictionary / ERD
- NFR / Security / Operations Standard

## Retrieval Strategy
1. 기존 PGM/ART relation
2. 관련 Source Symbol/Call/Data evidence
3. 기존 API/Batch/Interface/Repository Convention
4. Architecture/DB/Test/Security Standard
5. 유사 Program은 구조 참고만 하고 업무 Rule 근거로 사용하지 않는다.

## Steps
1. 기존 Program 재사용 가능성과 실제 Source target을 확인한다.
2. PGM Change Type/Spec Level/Entry Point를 정한다.
3. Physical Artifact/Symbol Evidence와 Source Hash를 연결한다.
4. Input/Output DTO의 기술 Envelope와 Domain Field 확정 상태를 분리한다.
5. Business Validation/Decision/State Transition/Calculation Rule을 기록한다.
6. Data/Table/Column, Transaction, Concurrency, Idempotency를 정의한다.
7. Integration/Notification이면 Message Schema/Timeout/Retry/DLQ를 정의한다.
8. Error Contract, Security, Audit/Observability, NFR을 정의한다.
9. TASK/AC/TC를 연결한다.
10. `program-spec-readiness.json`의 DoR 항목을 평가해 `READY / PARTIAL / EXECUTION_GUARDED`를 판정한다.

## Output
- PGM list/spec + TASK candidates
- Program Readiness result
- Template: `sdlc/templates/core/program-spec.md`

## Quality Check
- 외부 요구사항 ID→FR→PGM→TASK→AC/TC가 연결되는가
- PGM과 실제 Artifact/Symbol 관계에 Evidence가 있는가
- Reference/SIMULATED Architecture를 실제 Source Evidence로 오인하지 않았는가
- Input/Output Domain Field가 강타입 구현 가능한 수준인가
- Business Rule/Validation/State Transition이 OPEN인지 CONFIRMED인지 구분되는가
- 실제 Table/Column과 Transaction/Concurrency/Idempotency가 정의됐는가
- Error/Security/Audit/NFR가 정의됐는가
- DoR OPEN 항목이 있는데 `READY`로 표시하지 않았는가

## Alert Conditions
- `OPEN_REAL_SOURCE`인 상태에서 Production Source write 시도
- 신규 Interface/Batch/Table
- High Risk scope expansion
- Program target ambiguity
- DTO/Business Rule/Table/External Contract 미확정
- Transaction/Idempotency 미확정 상태의 mutation/integration/batch
- DoR와 Readiness 상태 불일치

## Token Strategy
1. PGM 관련 FR/Functional Design
2. Source Summary + relevant symbol
3. 관련 Data/Interface/Standard Section
4. 전체 Repository 대신 필요한 Symbol/Contract만 확장

## Do Not
- 존재하지 않는 Program/Table/API를 사실처럼 만들지 않는다.
- `SIMULATED_REFERENCE_ARCHITECTURE`를 `OBSERVED_REAL_SOURCE`로 승격하지 않는다.
- `Map<String,Object>` Reference DTO를 Production Domain DTO가 확정된 것으로 취급하지 않는다.
- OPEN DoR 항목을 숨기고 `READY`로 표시하지 않는다.
- 다른 Logical Program을 무단으로 함께 수정하지 않는다.
