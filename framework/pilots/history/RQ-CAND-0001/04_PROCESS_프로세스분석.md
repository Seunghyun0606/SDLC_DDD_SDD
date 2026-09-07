# 04 PROCESS — 프로세스분석

## 문서 목적
요구사항과 Source 관찰을 섞지 않고 업무 흐름 후보를 만든다.

## 30초 요약
AS-IS는 실제 운영 프로세스가 제공되지 않아 OPEN이며, fixture에서 관찰되는 저장/조회 동작만 Technical Observation으로 기록한다.

## Workflow
`Trigger → AS-IS observation → TO-BE candidate → exception/open policy`

## 입력/Evidence
- Requirement: GIVEN
- AS-IS fixture save/query: SIMULATED_SOURCE_FIXTURE

## 본문
### AS-IS
- 업무 AS-IS: `OPEN` — 첨부 요구사항에 현행 프로세스 설명 없음
- 기술 fixture AS-IS: 근무계획 저장/조회 동작 존재

### TO-BE Process Candidate
1. 사용자/시스템이 최초 근무계획 생성을 요청한다. (`Trigger OPEN`)
2. 직원/기간 기존 계획 존재 여부 확인. (`ASM-PILOT-001`)
3. 기존 계획이 없으면 기본 근무스케줄 조회.
4. 기본 스케줄을 근무계획으로 저장.
5. 저장된 근무계획 반환/조회.

### Exception Candidate
- 기본 스케줄 미존재: OPEN
- 생성 권한/대상 제외: OPEN

## 미확정/Alert/Assumption
`ASM-PILOT-001`은 Source fixture 테스트를 위한 임시 가정이다.

## 관련 ID/Traceability
`FR-03 → PROC-PILOT-001 → INT-PILOT-001~004`

## 다음 작업
DISCOVERY에서 fixture Source의 file/symbol/table relation을 수집한다.
