# /change

자연어 변경을 `CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`로 구조화한다.

1. Target과 Before/After를 식별한다.
2. RQ/FR/BR/PROC/PGM/TASK/AC/TC 관계를 따라 영향 범위를 계산한다.
3. 기존 Source Evidence와 충돌하면 기존 설계/Knowledge를 `STALE` 처리한다.
4. 확정되지 않은 변경은 Alert/Assumption과 함께 진행하며 위험 Source write만 Guard한다.
5. 변경 원문과 provenance를 보존한다.
