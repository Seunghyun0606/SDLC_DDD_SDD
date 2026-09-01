# CR-PILOT-001 + STALE Propagation

## Change
월마감 이후 승인된 수정요청은 재집계 허용, FORCE_CLOSE는 제외.

## 의미분류
`BEHAVIOR_CHANGE` + `GIVEN`.

## 변경 직후
- Subject Snapshot revision 1→2.
- PROCESS/IMPACT/DESIGN/PROGRAM/TEST 기존 revision을 STALE.
- Source Write permission을 임시 DENY.
- 새 Impact에서 TB_ATT_CORRECTION_REQ와 Target Proof를 확인한 뒤 Draft Write ALLOW 복구.

```text
CR
→ Stage Evidence revision 증가
→ affected artifacts STALE
→ Impact/Target Proof 재계산
→ Work Unit 새 idempotency key
→ Draft Source Write
→ Test/Verify
```

기존 revision의 Work Unit을 재사용하지 않는다. Source/canonical revision이 바뀌므로 새 idempotency key와 Target Proof가 필요하다.
