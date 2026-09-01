# Requirement Reference

## Purpose
Requirement 원문과 External ID를 보존하고 FR을 테스트 가능한 행동으로 분해한다.

## Required Input
- Stage: `DECOMPOSE`
- RQ + Source Record/External ID

## Optional Input
- 기존 Knowledge / Project Overlay / Domain Overlay / PM 정보

## Retrieval Strategy
1. Canonical direct relation
2. 기존 Program/Process/BR summary
3. Trace/Static Analysis candidate
4. Relevant symbol/source snippet
5. 필요한 경우에만 full file

## Steps
1. 입력과 Evidence provenance를 분리한다.
2. 현재 Stage에 필요한 최소 결과를 만든다.
3. 미확정은 ALT/ASM 또는 CHECK_REQUIRED로 남긴다.
4. Canonical relation과 Artifact를 동기화한다.

## Output
- Canonical RQ/FR/AC candidate
- Template: `sdlc/templates/core/requirement-analysis.md`

## Quality Check
- RQ/FR/PGM/TASK/AC/TC 연결이 가능한가
- Source 기반 사실은 locator/confidence가 있는가
- Human Truth와 OBSERVED/INFERRED가 섞이지 않았는가

## Alert Conditions
- Evidence 없음 또는 충돌
- Target ambiguity
- Business Truth 미확정
- Scope expansion

## Token Strategy
Summary/Index/Trace를 우선하고 관련 Symbol만 확장한다.

## Do Not
- Source 구현을 Business Rule로 자동 확정하지 않는다.
- 존재하지 않는 Program/Table/API를 사실처럼 만들지 않는다.
- 정보 부족만으로 전체 Workflow를 중단하지 않는다.
