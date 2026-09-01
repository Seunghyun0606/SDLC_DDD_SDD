# Test Scenarios

| TC | 조건 | 기대결과 | AC |
|---|---|---|---|
| TC-P017-01 | 계획 485분, 월미마감 | 480분 반영 | AC-01/02 |
| TC-P017-02 | 월마감 + 승인수정요청 + NORMAL | 재집계 허용 | AC-03 |
| TC-P017-03 | 월마감 + 미승인/요청없음 + NORMAL | 예외, DB Write 없음 | AC-04 |
| TC-P017-04 | 월마감 + 승인수정요청 + FORCE_CLOSE | 예외, DB Write 없음 | AC-05 |

이 파일은 CR 이전 rev1에서 `10분 반영` Case만 있었으나 CR 이후 3개 정책 Case를 추가해 CURRENT로 만들었다.
