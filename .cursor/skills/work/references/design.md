# Design Reference

## Purpose
구현 Method가 아니라 목표 시스템 동작을 정의하고 AS-IS Evidence와 TO-BE를 연결한다.

## Required Input
- Stage: `DESIGN`
- RQ/FR/AC + Process + Impact + Evidence

## Optional Input
- NFR/Standard/Interface Convention

## Retrieval Strategy
1. RQ/FR/AC
2. Process/Impact
3. Source Evidence
4. 관련 Standards

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR/AC, Process, Impact, AS-IS Evidence, TO-BE 요구, 적용 Standard/NFR를 확인한다. |
| 근거 분류 | 기존 Source 동작은 OBSERVED, 승인된 목표 동작은 GIVEN/CONFIRMED, 미확정 설계 선택지는 INFERRED/ASSUMED로 구분한다. |
| 실행 순서 | AS-IS 요약 → TO-BE 정상 흐름 → 예외/상태 변화 → I/O/Validation → Data/Transaction/Auth/Interface → NFR → AC Mapping 순서로 작성한다. |
| 계속/중단 조건 | 일부 NFR/정책이 OPEN이어도 설계 가능한 범위는 계속한다. 실제 Source가 필요한 AS-IS 항목은 근거 없이 채우지 않는다. |
| 출력 필드 매핑 | 기능 흐름, 입력/출력, 검증, 상태/예외, 데이터/연계/권한/NFR, AC relation을 Functional Design에 기록한다. |
| 품질 게이트 | 구현 클래스명이 없어도 목표 동작이 검증 가능해야 하며, 모든 핵심 동작이 AC와 연결되고 AS-IS/TO-BE가 구분되어야 한다. |
| 미확정/실패 처리 | 정책/데이터/NFR 미확정은 OPEN, Source와 문서 충돌은 CONFLICT, Impact Coverage Gap은 설계 Alert로 유지한다. |

## Steps
1. Evidence 기반 AS-IS를 요약한다.
2. TO-BE 정상/예외 흐름을 정의한다.
3. Data/Transaction/Auth/Interface/NFR를 정의한다.
4. AC Mapping을 갱신한다.

## Output
- Functional Design
- Template: `sdlc/templates/core/functional-design.md`

## Quality Check
- 기능 동작과 구현 세부가 적절히 분리되는가
- AC가 목표 동작을 검증할 수 있는가

## Alert Conditions
- Impact gap
- Business Rule 미확정
- Security/NFR 위험

## Token Strategy
Requirement/Impact/Relevant Evidence/Standard만 사용한다.

## Do Not
- 실제 Source 근거 없이 기존 동작을 발명하지 않는다.
- 미확정 정책을 CONFIRMED로 쓰지 않는다.
