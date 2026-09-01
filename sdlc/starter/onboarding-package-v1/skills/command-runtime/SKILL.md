# Skill — Command Runtime

## Purpose
`/work`, `/change`, `/check`를 capability plan→provider invocation→command result로 연결한다.

## Required Input
- command runtime context
- provider registry

## Steps
1. command capability plan 생성
2. missing/unavailable capability 확인
3. blocking Human Action 확인
4. capability별 Provider Request 생성
5. P0.8 runtime invoke
6. journal/result 집계
7. COMPLETE/PARTIAL/ACTION_REQUIRED/RECOVERY_REQUIRED 판정

## Rules
- command 이름으로 Adapter를 hardcode하지 않는다.
- blocking Human Action은 실행 중지, non-blocking은 병행 가능
- UNKNOWN_AFTER_WRITE 하나라도 있으면 RECOVERY_REQUIRED
- Provider PARTIAL은 전체 PARTIAL
- external capability 없는 /check는 local COMPLETE 가능

## Do Not
- missing Provider 결과 발명
- Human blocker 우회
- Business Truth/Canonical ID/Test PASS 생성
- Pilot-specific schema 추가
