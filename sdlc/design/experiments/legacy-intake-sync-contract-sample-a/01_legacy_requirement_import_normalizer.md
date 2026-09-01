# 01. Legacy Requirement Import Normalizer Contract

> 상태: `EXPERIMENT`
> 적용 대상: 기존 프로젝트에서 전달받은 Excel/CSV 요구사항 목록
> 목표: 원본 문서 의미를 훼손하지 않고 Canonical RQ/FR 후보를 만든다.

## 1. 문제 정의

Legacy 프로젝트의 요구사항 목록은 다음이 혼재할 수 있다.

- 상위 사업 요구
- 화면/CRUD 기능
- 프로그램 변경 목록
- Interface/Batch 항목
- PM Task
- 단순 Inventory

따라서 `1 Row = 1 RQ`를 Core Contract로 두면 다음 실패가 가능하다.

```text
Inventory Row
→ RQ 자동 발행
→ RQ 142건 과분해
→ 동일 Business Goal 중복
→ Process/BR/AC 중복 생성
→ Task/Metric 왜곡
```

반대로 `같은 요구사항명 = 1 RQ`를 자동 확정하면 39개 기능이 하나의 Mega-RQ가 되는 문제가 생긴다.

## 2. Normalizer Output Level

Import 직후에는 Canonical Published Entity가 아니라 다음 Candidate Layer를 사용한다.

```text
RAW_ITEM
  ├─ source_document
  ├─ source_sheet
  ├─ source_row
  ├─ source_item_id
  └─ raw_fields
        ↓
RQ_CANDIDATE_GROUP
        ↓
FR_CANDIDATE
        ↓
HUMAN_REVIEW
        ↓
PUBLISHED RQ / FR
```

### 2.1 RAW_ITEM

필수:

- `raw_uid`
- `source_document`
- `source_sheet`
- `source_row`
- `source_item_id`
- `source_hash`
- `raw_fields`
- `imported_at`

원칙:

- Raw 값은 정규화 전 원문을 보존한다.
- 기존 요구사항 ID는 Canonical Display ID로 재사용하지 않는다.
- 원본 ID는 `source_item_id`로 유지한다.

### 2.2 RQ_CANDIDATE_GROUP

현재 Sample A의 Overlay 제안:

```yaml
group_by:
  - 업무 대분류
  - 업무 중분류
  - 요구사항명
```

Candidate 필드:

- candidate_uid
- proposed_title
- source_raw_uids
- source_item_ids
- business_level1
- business_level2
- candidate_reason
- candidate_confidence
- candidate_status
- split_review

`candidate_status`:

- `PROPOSED`
- `REVIEWED`
- `PUBLISHED`
- `REJECTED`

### 2.3 FR_CANDIDATE

현재 Sample A에서는 `세부 요구사항`을 FR Candidate로 제안한다.

단, 다음은 자동 확정하지 않는다.

- 단순 CRUD가 정말 독립 FR인지
- 동일 동작의 조회/등록/수정이 하나의 FR인지
- Batch/Interface 항목이 기능인지 기술 Task인지
- 구현 항목이 상위 Business Requirement에 직접 대응하는지

## 3. Input Mapping Overlay

Core는 Column 이름을 고정하지 않는다.

```yaml
input:
  sheet: 원본요구사항
  header_row: 1
  columns:
    sequence: No
    business_level1: 업무 대분류
    business_level2: 업무 중분류
    source_item_id: 기존 요구사항 ID
    title: 요구사항명
    detail: 세부 요구사항
    planned_start: 시작일
    planned_end: 종료일
    assignee: 담당자
```

Normalizer는 다음 문자를 비교용 값에서만 정규화한다.

- 앞뒤 공백
- NBSP
- 연속 공백
- 줄바꿈 차이

그러나 Raw 원문은 반드시 별도 보존한다.

## 4. Grouping Rule

### Rule A — Exact normalized grouping

`업무 대분류 + 업무 중분류 + 요구사항명` 정규화 값이 같으면 동일 RQ Group Candidate로 묶는다.

### Rule B — No semantic auto-grouping by default

유사도만으로 다른 `요구사항명`을 자동 합치지 않는다.

예:

- `선택적근무관리 반영을 구현`
- `선택적근무관리 반영하는 기능`

은 유사하지만 자동 Merge하지 않는다. `DUPLICATE_GROUP_REVIEW` 후보로만 표시한다.

### Rule C — Mega-RQ Split Review

다음 중 하나면 `SPLIT_REVIEW_REQUIRED`를 표시한다.

- FR Candidate > 12
- Batch / Interface / UI / Core Transaction 등 서로 다른 technical boundary가 혼재
- 승인/반려/취소 등 상태전이가 다수 포함
- 하나의 Group 안에 서로 다른 Actor가 명시 또는 추론됨

현재 Sample에서는 최소 다음이 해당한다.

- `REQ_TM_TE016~054` / 39개
- `REQ_TM_TE055~076` / 22개
- `REQ_TM_TE077~099` / 23개

Normalizer는 **Split 필요성을 표시만 하고 자동 Split하지 않는다.**

## 5. Intake Quality Rule

v1.5.1의 사용자 최소 입력인 `요구사항명 / 현재 문제 또는 요청내용 / 원하는 결과`와 비교한다.

Sample은 `현재 문제`, 명시적 `원하는 결과`, `유지 조건`이 비어 있으므로 모든 Candidate는 기본적으로:

```text
Progress = WORKING
Quality = WARNING
Validity = CURRENT
```

으로 시작한다.

`현재 문제`와 `원하는 결과`가 Human Review에서 보완되기 전 `Quality=OK`로 승격하지 않는다.

## 6. Stage Handoff Contract

| 다음 Stage | Import 결과만으로 허용 | 금지 |
|---|---|---|
| DECOMPOSE | FR Candidate 초안 | RQ/FR 무검토 확정 |
| CLARIFY | 질문/Alert 생성 | BR CONFIRMED |
| PROCESS | Process Draft | AS-IS/TO-BE 확정 |
| DISCOVERY | Source 탐색 Query 생성 | Source 없는 Discovery COMPLETE |
| IMPACT | Business/Technical Candidate seed | Impact CONFIRMED |
| DESIGN | Design Skeleton | Tx/Auth/NFR 확정 |
| PROGRAM | Program 탐색 조건 생성 | PGM 자동 확정 |
| DEVELOPMENT | 없음 | Source Write |
| TEST | TC Candidate seed | Expected Result 확정 |
| VERIFY | 없음 | PASS |
| KNOWLEDGE | K3 Historical Evidence | K1/K2 Promotion |

## 7. Sample Expected Mapping

### Case A — FL001~003

```text
RQ Candidate
탄력근로제 개선 최초근무계획 자동 설정하는 기능

FR Candidate
- 탄력근로제 근무계획 저장
- 탄력근로제 근무계획 조회
- 기본 근무스케줄에 따라 근무계획 생성 자동 저장
```

Expected:

- RQ Candidate 1
- FR Candidate 3
- `INTAKE_MISSING_PROBLEM`
- `INTAKE_MISSING_DESIRED_OUTCOME`
- `CLARIFICATION_REQUIRED`

### Case B — FL014~021

Expected:

- RQ Candidate 1
- FR Candidate 8
- Process Draft 가능
- 승인/반려/취소/전자결재 상태전이 질문 생성
- Human 확인 없이 Process CONFIRMED 금지

### Case C — TE016~054

Expected:

- RQ Candidate 1
- FR Candidate 39
- `SPLIT_REVIEW_REQUIRED=true`
- 자동으로 여러 RQ로 Split하지 않음

### Case D — TE077~099

Expected:

- RQ Candidate 1
- FR Candidate 23
- `SPLIT_REVIEW_REQUIRED=true`
- `SOURCE_DISCOVERY_REQUIRED`
- Batch Schedule/Procedure/File/Table Consumer 질문 생성

## 8. Failure Conditions

다음은 Contract FAIL이다.

1. 142행을 자동 Published RQ 142건으로 생성
2. 원본 ID를 변경하거나 버림
3. Semantic similarity만으로 Group을 조용히 합침
4. 39개 Group을 사용자 확인 없이 자동 Split
5. Excel 문구를 근거로 BR을 `CONFIRMED` 처리
6. Source가 없는데 PGM/ART를 `CONFIRMED` 처리
7. 시작일/종료일/담당자 공란 때문에 Workflow 전체를 Block
8. Raw 원문과 정규화 값의 구분이 사라짐

## 9. Pilot Acceptance

Normalizer는 다음을 만족하면 Sample A 기준 PASS다.

- Raw 142행 보존율 = 100%
- 기존 ID 보존율 = 100%
- Expected RQ Candidate = 22
- Expected FR Candidate = 142
- Mega-RQ 3개 이상 Split Review 감지
- 자동 Published RQ = 0
- 자동 CONFIRMED BR = 0
- Source 없는 상태 Source Write = 0
- 시작일/종료일/담당자 null 허용 = 100%
