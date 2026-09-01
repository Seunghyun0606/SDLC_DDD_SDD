# 01 INTAKE — RQ-CAND-0001 요구사항

## 문서 목적
XLSX 원문을 손실 없이 RQ/FR 후보 입력으로 고정한다.

## 30초 요약
`탄력근로제 개선 최초근무계획 자동 설정하는 기능`에 속한 3개 외부 요구사항을 하나의 RQ Candidate로 그룹화했다.

## Workflow
`XLSX → normalize → exact title grouping → RQ Candidate`

## 입력/Evidence
| External ID | 요구사항명 | 요구사항 원문 | Truth/Evidence | Locator | Source Hash | Confidence | Status |
|---|---|---|---|---|---|---|---|
| REQ_TM_FL001 | 탄력근로제 개선 최초근무계획 자동 설정하는 기능 | 탄력근로제 근무계획 저장 | GIVEN | Sheet1!D3:F3 | sha256:d7dd76d786e97b66435bf4b9dc03fe04b8d55c580b565f2d45817893349ba39f | HIGH | CURRENT |
| REQ_TM_FL002 | 동일 | 탄력근로제 근무계획 조회 | GIVEN | Sheet1!D4:F4 | sha256:d7dd76d786e97b66435bf4b9dc03fe04b8d55c580b565f2d45817893349ba39f | HIGH | CURRENT |
| REQ_TM_FL003 | 동일 | 기본 근무스케줄에 따라 근무계획 생성 자동 저장 | GIVEN | Sheet1!D5:F5 | sha256:d7dd76d786e97b66435bf4b9dc03fe04b8d55c580b565f2d45817893349ba39f | HIGH | CURRENT |

## 본문
- RQ Candidate: `RQ-CAND-0001`
- Level1: 근태관리
- Level2: 근무계획 수립(탄력근로제)
- 외부 ID는 내부 ID로 대체하지 않는다.
- 담당자/시작일/종료일 공란은 유효한 Optional 입력으로 유지한다.

## 미확정/Alert/Assumption
없음. 이 단계에서는 원문 의미를 확장하지 않는다.

## 관련 ID/Traceability
`REQ_TM_FL001, REQ_TM_FL002, REQ_TM_FL003 → RQ-CAND-0001`

## 다음 작업
DECOMPOSE에서 구현기술과 독립적인 FR/AC 후보를 만든다.
