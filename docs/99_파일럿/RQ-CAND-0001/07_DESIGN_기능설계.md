# 07 DESIGN — 기능설계

> Source 관련 Evidence는 `SIMULATED_SOURCE_FIXTURE`다.

## 문서 목적
특정 Java 구현보다 먼저 목표 시스템 동작과 불확실성 경계를 정의한다.

## 30초 요약
저장/조회는 유지하고 자동 생성은 기본 스케줄 조회→계획 저장→결과 반환 흐름으로 설계한다. Trigger/예외 정책은 OPEN이다.

## Workflow
`FR/AC + Impact + Source Evidence → Functional Design`

## 입력/Evidence
- Requirement: GIVEN
- Service/Mapper/Table: SIMULATED_SOURCE_FIXTURE
- Service Hash: sha256:490fd18a0e8a006d71805e9675dfd0707b764bb63fdd3758a128d76f1313fab4

## 본문
1. 자동 생성 요청 수신. (`Trigger OPEN`)
2. 기존 계획 조회. (`ASM-PILOT-001`)
3. 계획이 없으면 기본 스케줄 조회.
4. 기본 스케줄로 계획 저장.
5. 저장 결과 반환.

Data: `TB_TM_FLEX_PLAN` READ/WRITE, `TB_TM_DEFAULT_SCHEDULE` READ.

Authorization/Audit/NFR: 요구사항 근거 없음 → OPEN.

## 미확정/Alert/Assumption
`ASM-PILOT-001`: 기존 계획 존재 시 기존 계획 반환. 실제 정책 확인 전 WARNING.

## 관련 ID/Traceability
`RQ → FR → AC → PROC → IMPACT → DESIGN`

## 다음 작업
PROGRAM에서 Logical Program/Artifact/TASK 단위로 구체화한다.
