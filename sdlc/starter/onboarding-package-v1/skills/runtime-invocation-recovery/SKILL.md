# Skill — Runtime Invocation / Recovery

## Purpose
Validated Provider Request를 실제 Adapter 호출로 연결하고 Journal/Retry/Recovery 상태를 보존한다.

## Required Input
- Provider Registry
- Validated Provider Request

## Preconditions
- exact capability provider가 AVAILABLE/DEGRADED
- write는 expected revision, permission proof, idempotency key 보유

## Atomic Steps
1. Request validation
2. exact Provider 선택
3. Adapter module load
4. Journal STARTED 기록
5. invoke
6. Response validation/correlation
7. OK/PARTIAL/BLOCKED/ERROR 분류
8. read-only retry policy 적용
9. write response unknown이면 UNKNOWN_AFTER_WRITE
10. terminal journal 반환

## Decision Rules
- read retry는 provider retryable=true일 때만
- write 자동 retry 금지
- PARTIAL은 reasoning 가능, release/write completeness 근거로 사용 금지
- test outcome FAILED와 provider ERROR를 혼동하지 않음

## Quality Check
- attempt 수와 terminal state 일치
- response correlation 검증
- write unknown을 success/fail로 추측하지 않음

## Alerts
- UNKNOWN_AFTER_WRITE
- AMBIGUOUS_PROVIDER
- ADAPTER_LOAD_FAILED
- RESPONSE_INVALID

## Stop
- terminal state 도달

## Escalation
- UNKNOWN_AFTER_WRITE → ENGINEERING_OR_HUMAN
- repeated retryable failure → L3/Provider Owner

## Do Not
- write 자동 재시도
- Provider 결과 발명
- PARTIAL을 release-ready로 승격
- Pilot 업무값을 runtime core에 하드코딩
