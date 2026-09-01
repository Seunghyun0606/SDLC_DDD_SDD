---
revision: 2
validity: CURRENT
---
# Functional Design

## 정상 흐름
1. 월마감 여부 조회.
2. 월마감이면 FORCE_CLOSE를 우선 차단.
3. 일반 마감이면 승인 수정요청 존재 여부 확인.
4. 계획분을 10분 단위로 절삭.
5. `TB_ATT_DAILY` MERGE.
6. 마감상태 갱신.

## Transaction
월마감 검증부터 `TB_ATT_DAILY`/`TB_ATT_CLOSE` 변경까지 Service Transaction 하나로 처리한다.

## Authorization
승인 자체는 이 Program이 수행하지 않는다. 이미 `APPROVED`인 수정요청만 조회한다.

## Error
월마감 후 허용조건 미충족 시 Source 변경 없이 실패한다.

## AC Mapping
FR-P017-01→AC-01, FR-P017-02→AC-02, FR-P017-03→AC-03/04, FR-P017-04→AC-05.
