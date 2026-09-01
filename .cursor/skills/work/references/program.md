# Program Reference

## Purpose
기존 Program 재사용을 우선하고 실제 Artifact/Symbol 근거 없이 PGM/테이블을 발명하지 않는다. Program Spec은 단순 역할 설명이 아니라 **6하원칙 업무 시나리오를 실제 구현 상세로 변환하고 Production Source 구현 전 Definition of Ready를 판정할 수 있는 수준**으로 작성한다.

## Required Input
- Stage: `PROGRAM`
- Functional Design + 6W Business Scenario + Impact
- Source Evidence 또는 `OPEN_REAL_SOURCE`
- Project Architecture / Coding / DB / Test Standard
- 관련 AC/TC Candidate

## Optional Input
- Existing Program Summary
- UI/UX Guideline / Screen Inventory
- API/Batch/Interface Contract
- Data Dictionary / ERD / Common Code Dictionary
- NFR / Security / Operations Standard

## Retrieval Strategy
1. 관련 SCN/FR/Functional Design
2. 기존 PGM/ART relation
3. 관련 Source Symbol/Call/Data evidence
4. UI/Data/Common Code/API/Batch/Interface/Repository Convention
5. Architecture/DB/Test/Security Standard
6. 유사 Program은 구조 참고만 하고 업무 Rule 근거로 사용하지 않는다.

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | SCN/FR/Functional Design/Impact, Source Evidence, Architecture/UI/DB/Code/Test Standard, AC/TC를 확인한다. 실제 Source가 없으면 `OPEN_REAL_SOURCE`를 명시한다. |
| 근거 분류 | 실제 Symbol/Table/Code/API/Annotation은 OBSERVED, 승인된 업무/기능 규칙은 CONFIRMED/GIVEN, 구조 제안은 INFERRED/ASSUMED로 구분한다. |
| 실행 순서 | 6W 책임 확인 → 기존 PGM 재사용 → Entry Point/Target → 화면/필드 → CRUD → DTO → 핵심 Logic → Query/Data → Common Code → Transaction → Integration → Error/Security/NFR → TASK/AC/TC → 개발 상세 완성도 → 17 DoR 순서로 수행한다. |
| 계속/중단 조건 | OPEN 항목이 있어도 PARTIAL Program Spec은 작성한다. UI가 아닌 진입점은 화면 항목을 N/A+사유로 둘 수 있다. Source write는 실제 Target confidence와 Execution Guard가 충족될 때만 허용한다. |
| 출력 필드 매핑 | SCN/PGM ID, Entry Point, UI/Menu/Field, CRUD, DTO, Logic, Query/Table/Column, Common Code, Transaction, Integration, Error, Security, NFR, TASK/AC/TC, 개발 상세 완성도, 17-field DoR를 기록한다. |
| 품질 게이트 | 모든 OBSERVED 항목에 Evidence가 있고, 개발 상세 계약의 적용 가능한 항목이 RESOLVED 또는 명시적 OPEN이며, 17개 DoR 상태가 명시되어야 한다. OPEN 또는 simulated source가 있으면 READY가 아니어야 한다. |
| 미확정/실패 처리 | Source 미확정은 OPEN_REAL_SOURCE, 화면/Field/Rule/Table/Code/Query/Contract 미확정은 OPEN, 비적용은 N/A 사유 필수, Target ambiguity는 EXECUTION_GUARDED 또는 PARTIAL로 유지한다. |

## Steps
1. 연결된 6W Scenario에서 이 PGM이 책임지는 `누가/언제/어디서/무엇/어떻게/왜`를 확인한다.
2. 기존 Program 재사용 가능성과 실제 Source target을 확인한다.
3. UI이면 메뉴/화면/컴포넌트와 Field 상세를 Source 또는 승인 설계에 연결한다. 비UI이면 N/A 사유를 기록한다.
4. 사용자/시스템 행위를 CRUD Matrix로 분해한다.
5. Input/Output DTO와 Field→DTO→DB/API Mapping을 연결한다.
6. Business Validation/Decision/Calculation/State Transition을 실행 순서와 Decision Table 수준으로 기록한다.
7. 조회는 WHERE/JOIN/ORDER/GROUP/PAGING/권한 Filter와 실제 Mapper/Query/Table 근거를 기록한다.
8. 저장/변경/삭제 Data/Table/Column, Transaction, Concurrency, Idempotency를 정의한다.
9. 공통코드/기준정보의 Group/Value/사용 Field/조회 방식을 기록한다.
10. Integration/Notification이면 대상 Program/System, Message/API Schema, Timeout/Retry/DLQ/재처리를 정의한다.
11. Error Contract, Security, Audit/Observability, NFR을 정의한다.
12. TASK/AC/TC를 연결한다.
13. `developer-spec-contract.json`의 적용 가능한 상세 명세를 `RESOLVED / OPEN / N/A(사유)`로 평가한다.
14. 기존 `program-spec-readiness.json`의 17 DoR 항목을 평가해 `READY / PARTIAL / EXECUTION_GUARDED`를 판정한다.

## Output
- PGM list/spec + TASK candidates
- Developer Specification Completeness result
- Program Readiness result
- Template: `sdlc/templates/core/program-spec.md`

## Quality Check
- 6W Scenario→FR→PGM→TASK→AC/TC가 연결되는가
- 화면/Field/CRUD가 실제 사용자/시스템 행위를 설명하는가
- 핵심 Logic이 구현 순서와 Decision 조건으로 명확한가
- 조회 Query 조건/Join/Order/Paging과 Table/Mapper 근거가 있는가
- Common Code/기준정보 사용 여부가 명확한가
- 다른 Program/System 연계 필요 여부가 명확한가
- PGM과 실제 Artifact/Symbol 관계에 Evidence가 있는가
- Reference/SIMULATED Architecture를 실제 Source Evidence로 오인하지 않았는가
- Input/Output Domain Field가 강타입 구현 가능한 수준인가
- Business Rule/Validation/State Transition이 OPEN인지 CONFIRMED인지 구분되는가
- 실제 Table/Column과 Transaction/Concurrency/Idempotency가 정의됐는가
- Error/Security/Audit/NFR가 정의됐는가
- 개발 상세 OPEN 또는 DoR OPEN이 있는데 `READY`로 표시하지 않았는가

## Alert Conditions
- 6W Scenario와 구현 동작 불일치
- `OPEN_REAL_SOURCE`인 상태에서 Production Source write 시도
- 신규 Interface/Batch/Table/Common Code
- High Risk scope expansion
- Program target ambiguity
- UI/Field/CRUD/Query/Common Code 미확정
- DTO/Business Rule/Table/External Contract 미확정
- Transaction/Idempotency 미확정 상태의 mutation/integration/batch
- 개발 상세 완성도와 DoR/Readiness 상태 불일치

## Token Strategy
1. PGM 관련 SCN/FR/Functional Design
2. Source Summary + relevant symbol
3. UI/Data/Common Code/Interface/Standard Section
4. 전체 Repository 대신 필요한 Symbol/Contract만 확장

## Do Not
- 존재하지 않는 Screen/Program/Table/Common Code/API를 사실처럼 만들지 않는다.
- `SIMULATED_REFERENCE_ARCHITECTURE`를 `OBSERVED_REAL_SOURCE`로 승격하지 않는다.
- `Map<String,Object>` Reference DTO를 Production Domain DTO가 확정된 것으로 취급하지 않는다.
- OPEN 상세 명세/DoR 항목을 숨기고 `READY`로 표시하지 않는다.
- 다른 Logical Program을 무단으로 함께 수정하지 않는다.
