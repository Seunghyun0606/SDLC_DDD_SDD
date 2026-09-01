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
