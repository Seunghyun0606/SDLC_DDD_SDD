---
stage: DESIGN
progress: COMPLETE
quality: OK
validity: CURRENT
---
# Functional Design

1. 월마감 조회.
2. 월마감이면 FORCE_CLOSE 차단.
3. 일반 유형이면 APPROVED 수정요청 조회.
4. 허용 시 10분 단위 계획 반영.
5. 동일 Transaction 안에서 근태/마감상태 갱신.

## Action Permission
Design complete와 Development write permission은 독립. 본 문서 단독으로 Source Write하지 않는다. Impact의 Target Write Proof와 Work Unit 확보가 필요하다.
