# RQC-017 Requirement Analysis Draft

> 상태: `DRAFT`
> FR Candidate: 39
> Confirmed BR: 0

## 실제 FR Candidate 예

| FR Candidate | Legacy ID | 기능 문구 |
|---|---|---|
| FRC-017-001 | REQ_TM_TE016 | 월근태확인 조회 |
| FRC-017-002 | REQ_TM_TE017 | 일근태입력/마감 조회 |
| FRC-017-003 | REQ_TM_TE018 | 일근태입력/마감 신청 등록 |
| FRC-017-004 | REQ_TM_TE019 | 일근태입력/마감 신청 수정 |
| FRC-017-005 | REQ_TM_TE020 | 일근태입력/마감 신청 삭제 |
| FRC-017-006 | REQ_TM_TE021 | 일근태입력/마감 강제마감 수정 |
| FRC-017-007 | REQ_TM_TE022 | 일근태입력/마감 전자결재송신정보 조회 |
| FRC-017-008 | REQ_TM_TE023 | 일근태입력/마감 전자결재 송신 |
| FRC-017-009 | REQ_TM_TE024 | 일근태입력/마감 전자결재 수신 |
| ... | ... | 총 39건 |

각 FR은 `GIVEN / CANDIDATE`이며 Canonical Publish되지 않는다.

## Clarification Questions 예

1. 39개 항목이 모두 하나의 Business Goal을 공유하는가?
2. 업무를 시작하는 Actor/Trigger가 모두 같은가?
3. 일마감/월마감/전사마감/강제마감/선택적근로마감은 같은 State Machine인가?
4. 마감 이후 수정·재오픈·취소 조건은 무엇인가?
5. 강제마감/전사마감 권한 주체는 누구인가?
6. 전자결재 반려/취소/재요청 시 업무 상태는 어떻게 되는가?
7. 일부 흐름만 독립 검증·배포해야 하는가?

## Process Candidate

```text
[OPEN] 마감 Trigger
  ↓
[INFERRED] 근무계획/근태 데이터 확인
  ↓
[OBSERVED_FROM_TEXT] 일마감 / 월마감 / 전사마감 / 강제마감 / 선택적근로마감
  ↓
[OBSERVED_FROM_TEXT] 일부 흐름은 전자결재 송수신 포함
  ↓
[OPEN] 마감 후 수정/재오픈 정책
```

## Business Rule

Excel 문구만으로 Confirmed Business Rule은 0건이다.

## Next

`PROCESS_DRAFT` 및 `DISCOVERY_PREP`는 가능하지만 Canonical Publish와 Source Write는 불가하다.
