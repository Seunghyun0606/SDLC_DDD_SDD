# Discovery Reference

## Purpose
Static Analysis First로 관련 Source/Symbol/Data 후보와 Evidence locator를 수집한다.

## Required Input
- Stage: `DISCOVERY`
- RQ/FR + Source Profile + Repository

## Optional Input
- 기존 Trace/Program Summary/Knowledge/Overlay

## Retrieval Strategy
1. 기존 Index/Trace/Program Summary
2. Symbol/Mapper/DB/Interface candidate
3. Relevant source snippet
4. 필요한 경우에만 full file

## Steps
1. Source Profile의 roots/excludes를 적용한다.
2. 후보 Artifact/Symbol/Data를 수집한다.
3. Locator/Source Hash/Confidence/Status를 기록한다.
4. Business 의미는 Candidate로 유지한다.

## Output
- Trace/Program/Data candidates
- Template: `sdlc/templates/core/impact-analysis.md`

## Quality Check
- Source Evidence locator가 있는가
- Candidate와 CONFIRMED가 분리되는가

## Alert Conditions
- Source/Profile 불완전
- Trace 충돌
- Target ambiguity

## Token Strategy
Static Analysis/Index 결과로 후보를 줄인 후 Source를 읽는다.

## Do Not
- Repository 전체를 LLM으로 먼저 읽지 않는다.
- Source 구현을 Business Rule로 자동 확정하지 않는다.
