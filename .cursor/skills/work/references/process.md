# Process Reference

## Purpose
업무를 단순 단계 나열이 아니라 **누가·언제·어디서·무엇을·어떻게·왜**의 6하원칙으로 정의하고 AS-IS/TO-BE, State, Exception, Business Rule을 연결한다. Source 동작은 OBSERVED로 표기한다.

## Required Input
- Stage: `PROCESS`
- RQ/FR + Human Truth + 관찰된 흐름
- 가능한 범위의 Actor/Trigger/업무 목적

## Optional Input
- SOP/업무규정/운영매뉴얼 추출 결과
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보

## Retrieval Strategy
1. Canonical relation
2. SOP/업무문서 Candidate와 기존 Process/BR
3. 관련 Source trace
4. 필요한 Source snippet

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR, 6W 후보, Actor/Role/Profile, Trigger, AS-IS Evidence, TO-BE 요구, State/Exception 후보를 사용한다. |
| 근거 분류 | 고객/업무 문서의 정책은 GIVEN/CONFIRMED, Source 실행 흐름은 OBSERVED, Process 연결 추론은 INFERRED로 구분한다. |
| 실행 순서 | 6W 후보 수집 → 누가/언제/어디서 확정 → 무엇/어떻게 단계화 → 왜/업무목적 확인 → AS-IS/TO-BE → State/Exception → BR Candidate 연결 순서로 수행한다. |
| 계속/중단 조건 | 6W 일부가 미확정이어도 OPEN으로 계속한다. 누락된 Why를 Source 구현으로 추정하지 않는다. 업무 흐름 자체를 구성할 입력이 전혀 없으면 Source call graph를 업무 Process로 대신 사용하지 않는다. |
| 출력 필드 매핑 | SCN ID, Who/When/Where/What/How/Why, PROC 단계, Actor, Trigger, Pre/Post State, Exception, BR Candidate, Evidence, OPEN 항목을 기록한다. |
| 품질 게이트 | 모든 업무 시나리오에 6개 차원이 표시되고, 누락은 OPEN이며, 업무 단계와 기술 호출이 분리되고 정상/예외 흐름이 추적 가능한 근거를 가져야 한다. |
| 미확정/실패 처리 | Source와 고객 정책이 충돌하면 CONFLICT, 6W/Actor/State 미상은 OPEN, Source만 있는 규칙은 OBSERVED_BR_CANDIDATE로 유지한다. |

## Steps
1. `business-scenario-sixw-contract.json`에 따라 시나리오별 6W를 채운다.
2. 자연어 업무 정의 문장을 만든다: `<누가>가 <언제> <어디서> <무엇을> <어떻게> 한다. 그 이유는 <왜>이다.`
3. Actor/Role/Profile/권한과 Trigger/주기/마감 조건을 분리한다.
4. AS-IS와 TO-BE를 단계별 입력·판단·결과·상태로 작성한다.
5. State/Exception/BR Candidate/Data/기준정보를 연결한다.
6. 미확정은 ALT/ASM/OPEN으로 남긴다.

## Output
- SCN/PROC/BR candidate
- Template: `sdlc/templates/core/process-analysis.md`

## Quality Check
- 6하원칙이 모두 표시되는가
- Why가 업무 목적/의무를 설명하고 단순 기술 이유로 대체되지 않았는가
- 업무 흐름과 기술 호출 흐름을 혼동하지 않는가
- Source 관찰을 CONFIRMED Business Rule로 올리지 않았는가

## Alert Conditions
- 6W 핵심 항목 미확정
- Process gap
- 정책 충돌
- Actor/State 미확정

## Token Strategy
관련 RQ/FR/SOP Candidate/Process와 direct Source trace만 우선한다.

## Do Not
- 비어 있는 6W 항목을 상식으로 발명하지 않는다.
- Source call graph를 업무 Process 자체로 간주하지 않는다.
- 정보 부족만으로 전체 Workflow를 중단하지 않는다.
