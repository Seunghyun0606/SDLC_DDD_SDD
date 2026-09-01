# Program Reference

## Purpose
Functional Design의 업무/기능 의미를 다시 작성하지 않고 실제 구현 Target, Source/Data Mapping, 실행 제어, TASK/AC/TC/Source 연결과 구현 준비도를 만든다. 기존 Program 재사용을 우선하고 실제 Artifact/Symbol 근거 없이 PGM/테이블을 발명하지 않는다.

## Required Input
- Stage: `PROGRAM`
- Functional Design + 관련 FR/SCN reference
- Impact
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
1. Functional Design의 관련 Section/ID와 남은 OPEN
2. 기존 PGM/ART relation
3. 관련 Source Symbol/Call/Data evidence
4. UI/Data/Common Code/API/Batch/Interface/Repository Convention
5. Architecture/DB/Test/Security Standard
6. 유사 Program은 구현 패턴 참고만 하고 업무 Rule 근거로 사용하지 않는다.

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | Functional Design 기준점, FR/SCN reference, Impact, Source Evidence, Architecture/UI/DB/Code/Test Standard, AC/TC를 확인한다. 실제 Source가 없으면 `OPEN_REAL_SOURCE`를 명시한다. |
| 근거 분류 | 실제 Symbol/Table/Code/API/Annotation은 OBSERVED, 승인된 업무/기능 규칙은 Functional Design을 참조하고 재작성하지 않는다. 구현 구조 제안은 INFERRED/ASSUMED 또는 기술 제안으로 구분한다. |
| 실행 순서 | Functional Design 기준점 고정 → 기존 PGM 재사용/Target 확인 → 실제 Source Symbol → 구현 Mapping/Delta → Query/Table/Source 근거 → Transaction/Runtime Control → Integration 기술계약 → Error/Security/Observability → TASK/AC/TC/Source → DoR/Execution Guard 순서로 수행한다. |
| 계속/중단 조건 | OPEN이 있어도 PARTIAL Program Spec은 작성한다. 실제 Source Target이 불명확하면 Source write는 막고 Spec 작성은 계속한다. Source write는 Target confidence와 Execution Guard가 충족될 때만 허용한다. |
| 출력 필드 매핑 | Functional Design ref, PGM/Entry Point/Source Symbol, 구현 Mapping/Delta, Query/Table/Column/Mapper, Transaction/Concurrency/Idempotency, Integration 기술계약, Technical Control, TASK/AC/TC/Source, 구현 준비도를 기록한다. 6W/화면 의미/Field 의미/CRUD 의미/Business Rule은 Functional Design reference로 연결한다. |
| 품질 게이트 | Program Spec이 Functional Design을 복제하지 않고 실제 구현 추가정보만 갖는지 확인한다. 모든 OBSERVED 항목에 Evidence가 있어야 하며 OPEN 또는 simulated source가 있으면 READY가 아니어야 한다. |
| 미확정/실패 처리 | Source 미확정은 `OPEN_REAL_SOURCE`, Mapping/Query/Table/Code/Integration/Target 미확정은 OPEN, 비적용은 N/A 사유 필수, Target ambiguity는 EXECUTION_GUARDED 또는 PARTIAL로 유지한다. |

## Steps
1. Functional Design의 버전과 이 PGM이 담당하는 FR/SCN/Section을 기준점으로 고정한다.
2. 6W, 화면 의미, Field 의미, CRUD 의미, Business Rule, 논리 Data 요구를 Program Spec에 복사하지 않는다.
3. 기존 Program 재사용 가능성과 실제 Source Target을 확인한다.
4. 실제 파일/Symbol/Entry Point/Service/Repository/Mapper/API Client 위치를 연결한다.
5. 기능 설계의 Field/행위를 실제 UI Component/DTO/API/DB와 연결하고 **구현 차이가 있는 항목만** Delta로 적는다.
6. 실제 Query/Table/Column/Mapper/Repository와 WHERE/JOIN/ORDER/GROUP/PAGING/권한 Filter의 구현 근거를 연결한다.
7. Transaction, Concurrency, Idempotency, Retry, Runtime Config/Feature Flag 등 구현 제어를 정의한다.
8. Integration이 있으면 Protocol/Topic/API/File/Payload/Timeout/Retry/실패보관 등 기술 계약만 적는다.
9. Error Mapping, Security implementation, Audit/Observability, NFR 구현 반영을 정의한다.
10. TASK → AC → TC → 실제 변경 Source를 연결한다.
11. `program-spec-readiness.json`의 DoR를 평가해 `READY / PARTIAL / EXECUTION_GUARDED`를 판정한다.
12. Functional Design 자체에 업무 의미 변경이 필요하면 Program Spec에서 수정하지 말고 DESIGN/CLARIFY로 되돌리는 Change를 만든다.

## Output
- PGM implementation spec + TASK candidates
- Program Readiness result
- Template: `sdlc/templates/core/program-spec.md`

## Quality Check
- Functional Design 기준점과 버전이 명확한가
- Program Spec에 6W/업무 규칙/화면 의미가 불필요하게 복제되지 않았는가
- PGM과 실제 Artifact/Symbol 관계에 Evidence가 있는가
- Field/DTO/API/DB Mapping 차이가 명확한가
- Query/Table/Column/Mapper 근거가 있는가
- Transaction/Concurrency/Idempotency가 필요한 경우 정의됐는가
- Integration의 실제 기술계약이 필요한 경우 정의됐는가
- TASK/AC/TC가 실제 변경 Source와 연결되는가
- `OPEN_REAL_SOURCE` 또는 Target ambiguity가 있는데 READY로 표시하지 않았는가

## Alert Conditions
- Functional Design과 실제 구현 요구가 불일치
- `OPEN_REAL_SOURCE`인 상태에서 Production Source write 시도
- 신규 Interface/Batch/Table/Common Code
- High Risk scope expansion
- Program target ambiguity
- Query/Table/External Contract 미확정
- Transaction/Idempotency 미확정 상태의 mutation/integration/batch
- Program Spec에서 업무정책을 임의 변경하려는 경우

## Token Strategy
1. Functional Design의 관련 Section/ID만 읽는다.
2. 기존 PGM relation + Source Summary + relevant symbol을 우선한다.
3. UI/Data/Common Code/Interface/Standard는 구현에 필요한 부분만 확장한다.
4. 전체 Repository 또는 Functional Design 전체를 반복 요약하지 않는다.

## Do Not
- Functional Design의 업무 내용을 Program Spec에 복사해 두 번째 Source of Truth를 만들지 않는다.
- 존재하지 않는 Screen/Program/Table/Common Code/API를 사실처럼 만들지 않는다.
- `SIMULATED_REFERENCE_ARCHITECTURE`를 `OBSERVED_REAL_SOURCE`로 승격하지 않는다.
- OPEN/DoR 항목을 숨기고 READY로 표시하지 않는다.
- 다른 Logical Program을 무단으로 함께 수정하지 않는다.
