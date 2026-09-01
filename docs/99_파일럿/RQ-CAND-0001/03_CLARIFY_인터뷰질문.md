# 03 CLARIFY — 인터뷰 질문

## 문서 목적
개발 전에 결과를 바꿀 수 있는 업무 불확실성만 질문으로 분리한다.

## 30초 요약
질문에 답이 없어도 다음 단계는 진행하되, 관련 설계는 WARNING/Assumption으로 유지한다.

## Workflow
`FR/AC → uncertainty → question → answer or assumption`

## 입력/Evidence
- Requirement: GIVEN
- 아직 실제 업무 정책 답변 없음

## 본문
| 질문 ID | 질문 | 영향 | 기본 처리 |
|---|---|---|---|
| INT-PILOT-001 | “최초” 자동 생성은 언제 실행되는가? | API/UI/Batch 설계 | OPEN |
| INT-PILOT-002 | 같은 기간의 계획이 이미 있으면 skip/overwrite/merge 중 무엇인가? | 데이터 무결성 | OPEN |
| INT-PILOT-003 | 기본 근무스케줄이 없을 때 동작은 무엇인가? | Exception/AC | OPEN |
| INT-PILOT-004 | 생성 대상 직원/기간 예외 조건이 있는가? | BR/Validation | OPEN |

## 미확정/Alert/Assumption
파일럿 TO-BE fixture에서는 테스트 가능성을 위해 “기존 계획이 있으면 그대로 반환”을 `ASM-PILOT-001`로 사용한다. 실제 Business Truth가 아니다.

## 관련 ID/Traceability
`INT-PILOT-001~004 ↔ FR-CAND-0001-03`

## 다음 작업
PROCESS에서 OPEN 질문을 명시한 채 AS-IS/TO-BE 흐름을 구성한다.
