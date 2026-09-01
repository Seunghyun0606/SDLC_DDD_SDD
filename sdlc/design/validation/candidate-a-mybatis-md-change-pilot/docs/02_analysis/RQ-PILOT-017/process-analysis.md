---
revision: 2
validity: CURRENT
---
# Process Analysis

## TO-BE
```text
마감 요청
→ 월마감 여부 확인
  ├─ 미마감 → 10분단위 계획 집계 → 근태반영 → CLOSED
  └─ 월마감
      → FORCE_CLOSE ?
         ├─ YES → 거부
         └─ NO → 승인 수정요청 존재 ?
                   ├─ YES → 10분단위 재집계 → 근태반영
                   └─ NO → 거부
```

## CR 반영 지점
rev1에는 `월마감 이후` Branch가 OPEN이었다. CR-PILOT-001 수신 후 해당 State/Exception부터 수정했다.

## 미확정
- 승인 수정요청을 누가 승인하는지 Authority는 실제 운영 정책 확인 필요.
- Batch Trigger에서도 동일 Rule을 사용할지는 실제 Source/운영 확인 필요.
