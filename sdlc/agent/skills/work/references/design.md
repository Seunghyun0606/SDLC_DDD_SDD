# Design Reference

## Purpose
구현 Method 자체보다 목표 시스템 동작을 정의하되, 개발자가 화면/필드/CRUD/핵심 규칙/데이터/연계/권한/예외를 이해할 수 있는 수준으로 구체화하고 6하원칙 업무 시나리오와 연결한다.

## Required Input
- Stage: `DESIGN`
- RQ/FR/AC + 6W Business Scenario + Process + Impact + Evidence

## Optional Input
- SOP 추출 결과
- NFR/Standard/Interface Convention
- UI/UX guideline, Data Dictionary, Code Dictionary

## Retrieval Strategy
1. RQ/FR/AC + Business Scenario
2. Process/BR/SOP Candidate
3. Impact/Source Evidence
4. 관련 UI/Data/Interface/Code Standards

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR/AC, 6W Scenario, Process, Impact, AS-IS Evidence, TO-BE 요구, Standard/NFR/Code/Data 근거를 확인한다. |
| 근거 분류 | 기존 Source 동작은 OBSERVED, 승인된 업무/목표 동작은 GIVEN/CONFIRMED, 미확정 설계 선택지는 INFERRED/ASSUMED로 구분한다. |
| 실행 순서 | 6W Scenario 확인 → AS-IS → TO-BE → 화면/채널·동선 → 필드 → CRUD → 핵심 로직/Decision → Data/Query → 공통코드 → Integration → 권한/상태/예외 → NFR → AC 순서로 작성한다. |
| 계속/중단 조건 | 일부 항목이 OPEN이어도 가능한 범위는 작성한다. 비UI 기능은 화면 항목을 `N/A + 사유`로 둘 수 있다. 실제 Table/Code/API가 필요한 Brownfield 항목은 근거 없이 확정하지 않는다. |
| 출력 필드 매핑 | 6W, Entry Surface, UI Component, Field Catalog, CRUD Matrix, Core Logic, Query/Data, Common Code, Integration, Security/State/Exception, NFR, AC를 Functional Design에 기록한다. |
| 품질 게이트 | 개발자가 어떤 사용자가 어디서 어떤 값을 입력/조회하고 어떤 규칙으로 어떤 데이터가 처리되는지 설명할 수 있어야 한다. 각 개발 상세 차원은 RESOLVED/OPEN/N/A 중 하나여야 한다. |
| 미확정/실패 처리 | 정책/필드/코드/데이터/NFR 미확정은 OPEN, Source와 문서 충돌은 CONFLICT, 비적용은 N/A 사유 필수, Impact Coverage Gap은 Alert로 유지한다. |

## Steps
1. `business-scenario-sixw-contract.json`의 6W를 Functional Design의 업무 기준으로 고정한다.
2. Evidence 기반 AS-IS와 TO-BE 정상/예외 흐름을 정의한다.
3. UI이면 메뉴/화면/컴포넌트/사용자 동선을 정의하고, 비UI이면 API/배치/Event 진입점을 정의한다.
4. 사용자 노출 및 입력/출력 Field Catalog를 작성한다.
5. 기능별 CRUD와 수행 주체/선행조건/결과를 작성한다.
6. 핵심 Logic 처리 순서와 Decision Table을 작성한다.
7. Query 조건/정렬/조인/집계/페이징과 Data 저장 정책을 정의한다.
8. 공통코드/기준정보 및 Integration을 정의한다.
9. 권한/State/Validation/Exception/NFR를 정의한다.
10. AC Mapping과 개발 상세 명세 준비도를 갱신한다.

## Output
- Functional Design
- Template: `sdlc/templates/core/functional-design.md`
- Completeness Contract: `sdlc/design/contracts/developer-spec-contract.json`

## Quality Check
- 6W가 기능 동작의 기준으로 유지되는가
- 화면/필드/CRUD/핵심 로직이 분리되어 있는가
- Query/Data/Common Code/Integration 필요 여부가 명시되는가
- N/A에 사유가 있는가
- AC가 핵심 사용자/시스템 동작을 검증할 수 있는가

## Alert Conditions
- 6W Business Scenario gap
- 핵심 화면/필드/CRUD OPEN
- Business Rule 미확정
- 실제 Data/Common Code/Integration 근거 미확정
- Security/NFR 위험

## Token Strategy
Requirement/Scenario/Process/Impact/Relevant Evidence/Standard만 사용한다.

## Do Not
- 화면이 필요하다고 가정해 존재하지 않는 화면을 발명하지 않는다.
- 실제 Source/프로젝트 근거 없이 기존 Table/Common Code/API를 확정하지 않는다.
- 미확정 정책을 CONFIRMED로 쓰지 않는다.
