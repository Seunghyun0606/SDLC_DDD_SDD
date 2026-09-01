# Verify Reference

## Purpose
Requirement→Source→Test evidence chain을 확인하고 미검증 항목을 명시한다.

## Required Input
- Stage: `VERIFY`
- RQ/FR/AC/TC + Source/Build/Test Evidence

## Optional Input
- Runtime evidence / Operations review / Knowledge candidates

## Retrieval Strategy
1. Canonical trace
2. Implementation result
3. Test result
4. Source hash/freshness

## Steps
1. RQ→FR→PGM→ART/SYMBOL→TASK→AC→TC 관계를 확인한다.
2. Source/Build/Test Evidence를 대조한다.
3. Unverified/Deferred 항목을 명시한다.
4. 재사용 가능한 Knowledge Candidate를 추출한다.

## Output
- Verification Result + Knowledge candidates
- Template: `sdlc/templates/core/verification-result.md`

## Quality Check
- Evidence chain이 끊기지 않는가
- 미검증 항목이 숨겨지지 않았는가

## Alert Conditions
- Source freshness mismatch
- Test failure
- Confirmed truth conflict
- Release 위험

## Token Strategy
Canonical relation과 Verification evidence만 우선한다.

## Do Not
- Evidence 없는 항목을 VERIFIED로 표시하지 않는다.
- Release 위험 외 일반 Workflow 전체를 Hard Block하지 않는다.
