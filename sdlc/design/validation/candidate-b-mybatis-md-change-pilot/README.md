# Candidate B — MyBatis MD + Execution/Recovery Pilot

> 상태: `VALIDATION PILOT / NOT BASELINE`
> Parent 입력: `요구사항목록.xlsx` Pilot B
> 중요: Candidate B 단독은 Legacy Raw→RQ 경계를 만들지 않으므로 downstream 검증을 위해 `RQ-PILOT-017 Subject Snapshot`을 외부 Intake 결과로 GIVEN 입력한다. 이는 A와 결합한 것이 아니다.

## Quick Start

```text
input/RQ-PILOT-017_subject-snapshot.md
→ Stage Evidence가 포함된 Analysis/Impact/Design
→ PGM-ATT-CLOSE-001 Target Write Proof
→ Developer Work Group / PGM Serial Lane
→ Work Unit PREPARED
→ short-lived branch Draft Source Write
→ APPLIED 후 Runner Crash 시뮬레이션
→ 중앙 Journal에서 Resume Verify
→ Test/Verification
```

중간 변경:

```text
CR-PILOT-001
월마감 이후 승인된 수정요청은 재집계 허용.
FORCE_CLOSE는 제외.
```

B의 핵심은 변경 후에도 `progress=COMPLETE`와 `action_permissions`를 분리하는 것이다.

## Fixture Stack
- Java 17 / Spring Service
- MyBatis Interface + XML
- Oracle MERGE
- 동일 PGM에 2개 DEV Task를 두어 Serial Lane 검증
- Central Work Unit Store는 계약 시뮬레이션이며 실제 중앙 DB를 띄운 것은 아님

## 사용자가 볼 포인트
1. 문서 작성 완료와 실제 코드/병합/배포 가능 상태가 구분되는가.
2. 업무 변경 시 어느 Artifact가 STALE인지 명확한가.
3. 동일 PGM Task 배분과 Write 직렬화가 이해되는가.
4. Crash 후 patch 재적용 없이 복구되는 흐름이 이해되는가.
