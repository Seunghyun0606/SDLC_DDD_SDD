# 04. Validation Checklist — Sample A

> 사용법: 유저가 다른 Branch와 문서 설계를 비교할 때 각 항목을 `PASS / FAIL / N/A / NEEDS_EVIDENCE`로 표시한다.

## A. 문서 이해성

- [ ] 상단에 이 Branch가 Baseline이 아닌 실험안임이 보인다.
- [ ] `Raw Item → RQ Candidate → FR Candidate → Publish` 흐름을 1분 안에 이해할 수 있다.
- [ ] RQ와 FR의 차이를 Agent 비숙련 사용자도 이해할 수 있다.
- [ ] Source가 없어서 못 하는 단계와, 계속할 수 있는 단계가 구분된다.
- [ ] `WARNING / CANDIDATE / DRAFT / DEFERRED` 의미가 문서에서 일관된다.

## B. Legacy Import

- [ ] 142개 Raw Row가 모두 보존된다.
- [ ] `REQ_TM_*` 기존 ID가 모두 Provenance로 유지된다.
- [ ] 동일 요구사항명 Group Candidate 22개가 재현된다.
- [ ] 142행을 자동 Published RQ로 만들지 않는다.
- [ ] Similarity만으로 다른 제목을 자동 Merge하지 않는다.
- [ ] 39/22/23개 대형 Group에 Split Review가 표시된다.
- [ ] 자동 Split은 하지 않는다.
- [ ] Raw 원문과 비교용 정규화 값이 분리된다.

## C. Requirement / Analysis

- [ ] 현재 문제 누락을 Alert로 표시한다.
- [ ] 원하는 결과 누락을 Alert로 표시한다.
- [ ] 유지 조건/정책/예외/적용범위 질문이 생성된다.
- [ ] CRUD 문구를 그대로 Business Rule로 승격하지 않는다.
- [ ] 전자결재 Group에서 Actor/State/반려/취소 질문을 만든다.
- [ ] Batch Group에서 Schedule/재처리/Consumer 질문을 만든다.
- [ ] Interface Group에서 Payload/Auth/Retry/Privacy 질문을 만든다.

## D. Non-blocking Process

- [ ] 담당자 null이어도 PM 초안 생성 가능하다.
- [ ] 시작일/종료일 null이어도 Stage 진행 가능하다.
- [ ] 질문 미답변이어도 다음 Draft/Discovery 준비는 가능하다.
- [ ] 위험 Source Write만 Deferred/Guard 처리한다.
- [ ] 하나의 Conflict가 다른 RQ/Work Item 진행을 막지 않는다.

## E. Source-dependent Safety

- [ ] Source Repository가 없으면 DISCOVERY COMPLETE가 되지 않는다.
- [ ] Static Analyzer 결과가 없으면 IMPACT CONFIRMED가 되지 않는다.
- [ ] PGM/ART Evidence가 없으면 PROGRAM COMPLETE가 되지 않는다.
- [ ] Target Write Proof가 없으면 DEVELOPMENT Source Write가 0건이다.
- [ ] Test Result가 없으면 VERIFY PASS가 0건이다.
- [ ] Legacy Excel만으로 K1/K2 Promotion이 0건이다.

## F. 전체작업목록 UX

- [ ] 작업ID/상위작업ID/요구사항ID가 구분된다.
- [ ] 한글 Header가 직관적이다.
- [ ] 담당자/계획일정은 Optional로 보인다.
- [ ] RQ→FR→PGM→TASK→AC/TC Drill-down을 표현할 수 있다.
- [ ] 기존 Source Requirement ID를 별도 컬럼/Trace로 확인 가능하다.

## G. MD ↔ Excel Sync

- [ ] Stable ID 기반으로 동일 Work Item을 찾는다.
- [ ] revision/base revision이 정의된다.
- [ ] MD만 변경한 경우 반영 규칙이 있다.
- [ ] Excel만 변경한 경우 반영 규칙이 있다.
- [ ] 서로 다른 Field 동시변경은 병합 가능하다.
- [ ] 같은 Field 다른 값은 `SYNC_CONFLICT`가 된다.
- [ ] Timestamp Last-write-wins를 사용하지 않는다.
- [ ] 행 삭제가 Hard Delete로 바로 이어지지 않는다.
- [ ] Published 작업ID 임의변경을 허용하지 않는다.
- [ ] Generated Field 직접 수정은 Alert 후 무시된다.
- [ ] Null 담당자/일정이 왕복 후에도 null이다.

## H. 비교 평가 점수

각 항목 1~5점으로 평가한다.

| 평가축 | 점수 | 메모 |
|---|---:|---|
| 비숙련 사용자 이해성 |  |  |
| 기존 문서 수용성 |  |  |
| Canonical 추적성 |  |  |
| Non-blocking 적합성 |  |  |
| Silent Failure 방어 |  |  |
| PM 사용성 |  |  |
| Customizing 용이성 |  |  |
| 구현 난이도 |  |  |
| 운영 난이도 |  |  |
| 다른 프로젝트 재사용성 |  |  |

## I. Candidate A Reject 조건

다음 중 하나라도 구조적으로 해결하기 어렵다면 Candidate A를 채택하지 않는다.

- Raw→Candidate Layer가 사용자에게 지나치게 복잡함
- 22 Group Candidate가 실제 업무 RQ 구조와 크게 다름
- RQ/FR Candidate Review 비용이 원본 문서 수작업 정리보다 큼
- MD↔Excel 3-way Sync가 Pilot 규모 대비 과도함
- Legacy Source ID와 Canonical ID 이중 관리가 사용자 혼란을 크게 만듦
- Mega-RQ Split Review가 반복적으로 Human Bottleneck을 만듦

## J. 현재 Evidence 상태

첨부 요구사항목록으로 검증 가능:

- Import 구조
- Grouping Candidate
- Null 일정/담당자 처리
- Stage별 정보 충분성
- Clarification 질문 범주

추가 Evidence 필요:

- 실제 Source/Static Analyzer 기반 Discovery/Impact
- PGM/ART Target Resolution
- 실제 MD↔Excel Converter Round-trip
- Test/Verify
- Knowledge Reuse
- Merge/Concurrent Update
