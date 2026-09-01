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
