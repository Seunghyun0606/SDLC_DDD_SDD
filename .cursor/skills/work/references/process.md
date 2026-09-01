# Process Reference

## Purpose
AS-IS/TO-BE, Actor, Trigger, State, Exception을 구분하고 Source 동작은 OBSERVED로 표기한다.

## Required Input
- Stage: `PROCESS`
- RQ/FR + Human Truth + 관찰된 흐름

## Optional Input
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보

## Retrieval Strategy
1. Canonical relation
2. 기존 Process/BR
3. 관련 Source trace
4. 필요한 Source snippet

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR, Actor 후보, Trigger, AS-IS Evidence, TO-BE 요구, State/Exception 후보를 사용한다. |
| 근거 분류 | 고객/업무 문서의 정책은 GIVEN/CONFIRMED, Source 실행 흐름은 OBSERVED, Process 연결 추론은 INFERRED로 구분한다. |
| 실행 순서 | Actor/Trigger 식별 → AS-IS 단계화 → TO-BE 단계화 → State 변화 → Exception/분기 → BR Candidate 연결 순서로 수행한다. |
| 계속/중단 조건 | 일부 Actor/State가 미확정이어도 ALT/OPEN으로 계속한다. 업무 흐름 자체를 구성할 입력이 전혀 없으면 Source call graph를 대신 사용하지 않는다. |
| 출력 필드 매핑 | PROC 단계, Actor, Trigger, Pre/Post State, Exception, BR Candidate, Evidence, OPEN 항목을 기록한다. |
| 품질 게이트 | 업무 단계와 기술 호출이 분리되고, 정상/예외 흐름과 상태 변화가 최소 하나의 추적 가능한 근거를 가져야 한다. |
| 미확정/실패 처리 | Source와 고객 정책이 충돌하면 CONFLICT, Actor/State 미상은 OPEN, Source만 있는 규칙은 OBSERVED_BR_CANDIDATE로 유지한다. |

## Steps
1. Actor/Trigger를 식별한다.
2. AS-IS와 TO-BE를 분리한다.
3. State/Exception/BR Candidate를 연결한다.
4. 미확정은 ALT/ASM으로 남긴다.

## Output
- PROC/BR candidate
- Template: `sdlc/templates/core/process-analysis.md`

## Quality Check
- 업무 흐름과 기술 호출 흐름을 혼동하지 않는가
- Source 관찰을 CONFIRMED Business Rule로 올리지 않았는가

## Alert Conditions
- Process gap
- 정책 충돌
- Actor/State 미확정

## Token Strategy
Process 관련 Program summary와 direct trace만 우선한다.

## Do Not
- Source call graph를 업무 Process 자체로 간주하지 않는다.
- 정보 부족만으로 전체 Workflow를 중단하지 않는다.
