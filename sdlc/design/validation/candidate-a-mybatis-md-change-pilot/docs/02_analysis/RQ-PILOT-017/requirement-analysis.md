---
revision: 2
validity: CURRENT
source_change: CR-PILOT-001
---
# Requirement Analysis

## FR
- FR-P017-01: 마감 시 근무계획 분을 10분 단위로 반영한다.
- FR-P017-02: 월마감 여부를 확인한다.
- FR-P017-03: 월마감 후 승인된 수정요청이면 재집계를 허용한다.
- FR-P017-04: FORCE_CLOSE이면 월마감 후 재집계를 거부한다.

## Business Rule
- BR-P017-01 `CANDIDATE`: 반영 분은 10분 단위를 보존한다.
- BR-P017-02 `GIVEN`: 월마감 후 승인 수정요청만 재집계 가능하다.
- BR-P017-03 `GIVEN`: FORCE_CLOSE는 월마감 후 재집계 대상이 아니다.

## AC
- AC-01: 계획 485분은 480분으로 반영된다.
- AC-02: 월마감 전에는 승인 수정요청 없이 정상 마감 가능하다.
- AC-03: 월마감 후 승인 수정요청이 있으면 정상 마감 재집계가 가능하다.
- AC-04: 월마감 후 승인 수정요청이 없으면 실패한다.
- AC-05: 월마감 후 FORCE_CLOSE는 승인 수정요청이 있어도 실패한다.

## Change 영향
rev1의 `10분 반영`만으로는 AC-03~05를 설명할 수 없어 본 문서를 STALE 처리한 뒤 rev2로 재생성했다.
