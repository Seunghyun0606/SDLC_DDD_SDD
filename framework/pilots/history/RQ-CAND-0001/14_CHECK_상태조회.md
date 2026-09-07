# 14 CHECK — 사용자 상태조회 예시

## 문서 목적
사용자가 내부 복잡성을 몰라도 현재 Pilot 상태를 빠르게 이해하도록 한다.

## 30초 요약
파일럿 구조는 VERIFY까지 생성됐지만 실제 Source/Build/Test가 아니므로 완료로 오해하면 안 된다.

## Workflow
`Canonical/Artifact state → concise status view`

## 입력/Evidence
Pilot artifact state + SIMULATED_SOURCE_FIXTURE validation.

## 본문
### `/check RQ-CAND-0001` 예시
- 현재 단계: VERIFY 완료(파일럿 구조 기준)
- 품질: WARNING
- 유효성: CURRENT (Pilot Artifact)
- Open Alert: INT-PILOT-001~004
- Active Assumption: ASM-PILOT-001
- Source Evidence: SIMULATED_SOURCE_FIXTURE
- 실제 Application Test: 미수행
- 다음 추천: 실제 Brownfield Source 연결 후 DISCOVERY부터 재실행

## 미확정/Alert/Assumption
실제 Application Evidence가 들어오면 fixture 기반 DISCOVERY 이후 문서는 STALE 처리 후 재생성한다.

## 관련 ID/Traceability
`RQ-CAND-0001 → current stage/alerts/next action`

## 다음 작업
실제 Source Repository/Profile을 연결한다.
