# 02. MD ↔ Excel Bidirectional Sync Contract

> 상태: `EXPERIMENT`
> 대상 View: `docs/00_관리/전체작업목록.md`, `docs/00_관리/전체작업목록.xlsx`
> Canonical은 의미 원장이고 MD/Excel은 사용자 View라는 v1.5.1 원칙을 유지한다.

## 1. 목표

사용자가 MD 또는 Excel 어느 쪽을 수정하더라도 다음을 만족해야 한다.

1. 동일 Work Item Identity 유지
2. 변경 유실 방지
3. 충돌 Silent Overwrite 금지
4. 한글 사용자 Header 유지
5. 담당자/일정 Optional 유지
6. Generated Field와 Human Field 구분
7. Import/Export 반복 후 의미 보존

## 2. Sync Unit

기본 Sync Unit은 `Work Item + Field`다.

Canonical key:

- `work_item_uid`: 내부 UID
- `work_item_id`: 사용자 Stable ID
- `revision`: Canonical 변경 버전
- `updated_at`: Canonical 최근 변경시각

View Metadata:

- `view_base_revision`: 해당 View가 생성된 Canonical revision
- `view_generated_at`
- `view_hash`

MD/Excel에 내부 UID를 반드시 노출할 필요는 없지만 Import 시 Stable ID와 View Metadata로 동일 Entity를 찾아야 한다.

## 3. Field Ownership

### Human-editable

- 작업명
- 담당자
- 계획시작일
- 계획종료일
- 예상공수
- 상태 중 Human-managed 값
- 비고

### Harness-derived / Generated

- 최근변경일시
- 변경버전
- 일부 품질상태
- 유효상태
- 자동 계산 Coverage

Generated Field가 View에서 임의 수정되면 `GENERATED_FIELD_EDIT` Alert를 생성하고 Canonical을 조용히 덮어쓰지 않는다.

## 4. Import Algorithm

```text
MD 또는 Excel Import
→ Stable ID 조회
→ View Base Revision 확인
→ Canonical Current와 Diff
→ Field별 변경 분류
→ Auto Apply / Conflict / Ignore Generated Edit
→ Canonical Revision 증가
→ MD + Excel 재생성
```

### Case 1 — 한 View만 변경

`view_base_revision == canonical_revision`이고 사용자 Field가 바뀌었으면 적용 가능.

### Case 2 — Canonical이 먼저 변경됨

View가 오래된 상태이면 `base → current → incoming` 3-way 비교를 수행한다.

### Case 3 — 서로 다른 Field 변경

예:

- MD: `비고` 변경
- Excel: `담당자` 변경

동일 Base에서 서로 다른 Field를 변경했다면 자동 병합 가능하다.

### Case 4 — 같은 Field를 서로 다르게 변경

예:

- MD 담당자 = `홍길동`
- Excel 담당자 = `김영희`

결과:

```text
SYNC_CONFLICT
field = assignee
resolution = USER_DECISION
```

어느 쪽도 최신이라는 이유만으로 자동 승리시키지 않는다.

## 5. Row/Entity Operations

### 신규 행

새 `작업ID`가 없으면 Import Candidate로 만들며 ID 발급 정책에 따라 Canonical Publish한다.

### 삭제 행

View에서 행이 사라졌다는 이유만으로 Canonical Entity를 Hard Delete하지 않는다.

- `DELETE_CANDIDATE`
- Human Review 또는 명시적 Change 필요

### ID 변경

Published `작업ID` 변경은 기본 금지.

오타 정정이 필요하면 Internal UID 유지 + Alias/Redirect 정책을 사용하고 별도 Decision 대상으로 둔다.

## 6. Legacy Source ID와 Work Item ID

Sample Excel의 `REQ_TM_FL001` 등은 기존 시스템의 Source Requirement ID다.

이 값은 다음과 같이 별도 보존한다.

```text
source_item_id = REQ_TM_FL001
canonical_work_item_id = FR-xxxx-xx  # Publish 후
```

기존 ID와 Canonical ID를 하나의 필드에 혼용하지 않는다.

## 7. 한글 Header Contract

사용자 View는 v1.5.1의 `worklist-columns.yaml`을 따른다.

예:

- 작업ID
- 상위작업ID
- 요구사항ID
- 작업구분
- 작업명
- 단계
- 상태
- 품질상태
- 유효상태
- 담당자
- 계획시작일
- 계획종료일
- 예상공수
- 관련프로그램ID
- 완료기준ID
- 경고·확인사항
- 최근변경일시
- 변경버전
- 비고

내부 key 변경 없이 label만 Project Overlay로 바꿀 수 있어야 한다.

## 8. Round-trip Invariants

다음은 MD→Canonical→Excel→Canonical→MD 왕복 후 유지되어야 한다.

| Invariant | 기준 |
|---|---|
| Work Item Identity | 100% 동일 |
| Parent Relation | 100% 동일 |
| Source Requirement ID | 100% 보존 |
| 한글 Header | Mapping Contract 일치 |
| Null 담당자/일정 | Null 그대로 보존 |
| User Text | 의미 있는 Trim 외 무손실 |
| Revision | 변경이 있을 때만 증가 |
| Conflict | 동일 Field 경쟁 변경을 100% 탐지 |
| Silent Delete | 0건 |
| Silent Overwrite | 0건 |

## 9. Sync Conflict Test Cases

### SYNC-01 — Excel Only Update

- Base 담당자: null
- Excel: 담당자 `A`
- MD: 변경 없음
- Expected: APPLY / revision +1

### SYNC-02 — MD Only Update

- Base 비고: null
- MD: 비고 추가
- Excel: 변경 없음
- Expected: APPLY / revision +1

### SYNC-03 — Non-overlapping Concurrent Update

- MD: 비고 변경
- Excel: 담당자 변경
- Expected: AUTO_MERGE / revision +1

### SYNC-04 — Same-field Conflict

- MD 담당자 `A`
- Excel 담당자 `B`
- Expected: `SYNC_CONFLICT`, Canonical 미변경, 다른 Work Item 진행 가능

### SYNC-05 — Stale View

- Excel base revision 3
- Canonical current revision 5
- Excel이 revision 3 기준 값을 변경
- Expected: 3-way diff 후 Conflict 또는 안전 Apply

### SYNC-06 — Generated Field Edit

- Excel `변경버전` 직접 수정
- Expected: `GENERATED_FIELD_EDIT`, 값 무시, Alert 기록

### SYNC-07 — Row Delete

- MD에서 기존 행 삭제
- Expected: Hard Delete 금지, `DELETE_CANDIDATE`

### SYNC-08 — Published ID Edit

- Excel `작업ID` 변경
- Expected: `IMMUTABLE_ID_VIOLATION`

## 10. Failure Conditions

다음 중 하나면 Candidate A Sync Contract FAIL이다.

1. Timestamp 최신값만으로 충돌 해결
2. 같은 Field의 다른 값이 조용히 overwrite
3. 행 삭제가 Canonical Hard Delete로 바로 반영
4. Published ID 변경 허용
5. 담당자/일정 null을 강제 채움
6. Generated Field 수정이 Canonical에 반영
7. MD와 Excel의 Work Item 수가 이유 없이 달라짐
8. Legacy Source ID가 Export 과정에서 소실

## 11. 실제 Converter 구현 전 검증 범위

이 Branch는 **문서/계약 설계안**이다.

PASS로 볼 수 있는 것:

- Sync 상태모델이 모순 없이 정의됨
- 동시수정/삭제/ID변경 실패행동이 명확함
- Sample Requirement의 null 일정/담당자를 수용함

아직 PASS로 볼 수 없는 것:

- 실제 `.xlsx` Round-trip 정확도
- Markdown Parser 안정성
- Formula/Format 보존
- 대량 행 성능
- Process Crash 후 Recovery

실제 Converter Spike에서는 위 Round-trip Invariant를 자동 Test로 구현해야 한다.
