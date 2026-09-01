# 09. Development Blueprint Guide

Development Blueprint는 개발자가 별도 추측 없이 구현/질문/Target을 이해할 정도의 상세설계다. Context/Evidence Pack은 Blueprint+Source Evidence의 Manifest다.

## 필수 12영역
1. 6W Business Scenario
2. Screen/Channel
3. Field Specification
4. CRUD Matrix
5. Core Business Logic/Decision Table
6. State/Validation/Error
7. Integration
8. Query/Data
9. Common Code
10. Transaction/Auth/Audit
11. Brownfield Source Mapping
12. Test Mapping

## UI
변경 없음도 구분:
- `NO_UI_CHANGE_CONFIRMED`
- `NO_UI_CHANGE_ASSUMED`
- `OPEN`

## Query/Data
- 목적
- Parameter
- Table/View/Procedure
- Key/Join/Filter
- Null/default
- Lock/concurrency
- Index/cardinality
- Read/Write

## Common Code
- Concept
- Group
- actual value
- Evidence
- hardcode 여부

실제 Code가 확인되지 않으면 symbolic name을 Source에 하드코딩하지 않는다.

## Source-ready Gate
각 영역: `PASS / PARTIAL / OPEN / NOT_APPLICABLE`

Critical OPEN:
- 실제 권한/Profile
- 실제 공통코드
- PK/UK/Lock
- Interface 계약
- Transaction
- Target revision

Patch Proposal과 실제 Write를 구분한다.
