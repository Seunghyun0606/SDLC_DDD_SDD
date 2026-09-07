# Engineering Work Map

> 이 문서는 Canonical Spec 기반의 개발/설계용 Living Spec입니다. 단순 오탈자 외의 설계·동작 변경을 직접 편집하지 않습니다. 설계/Source Mapping 보완은 `/work`, 요구사항·Business Rule·TO-BE 동작 변경은 `/change`로 처리합니다.
>
> **Work Unit은 업무/기능 변경 경계이고 Program은 구현 단위입니다.** 하나의 Work Unit이 여러 Program/Source를 포함할 수 있으며, 화면 수나 파일 수만으로 Work Unit을 쪼개지 않습니다.
>
> **사용자는 이 Template의 빈칸을 직접 채우지 않습니다.** Agent가 먼저 초안을 만들고 필요한 질문만 요청합니다. 수정이 필요하면 `이 문서의 [BLOCK:WM-MAPPING]을 ...로 바꿔줘`처럼 Block을 지정합니다. 즉시 답할 수 없는 질문은 Agent가 `WM-HITL-QUEUE`에 남기고 다음 Semantic Work에서 재확인합니다.

**Block ID:** `WM-SUMMARY`, `WM-UNIT`, `WM-MAPPING`, `WM-AC-TEST`, `WM-OPEN`, `WM-HITL-QUEUE`, `WM-NEXT`

<!-- BLOCK_ID: WM-SUMMARY -->
## 1. 요구사항 요약
- 무엇이 왜 바뀌는가:
- 기대 결과:
- 유지 조건/제외 범위:

<!-- BLOCK_ID: WM-UNIT -->
## 2. 업무·기능 단위
| Work Unit | 기능 목적 | 경계/분할 근거 | 관련 RQ/FR/FTR | Program 수 | 상태 |
|---|---|---|---|---:|---|
|  |  |  |  |  |  |

<!-- BLOCK_ID: WM-MAPPING -->
## 3. Engineering Mapping
| Work Unit | Work Package | Design Task | Development Task | Test Task | Program | Source | 담당 | 상태 |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

<!-- BLOCK_ID: WM-AC-TEST -->
## 4. AC / Test 연결
| Acceptance Criteria | Test Case/Scenario | 검증 Evidence | 결과 |
|---|---|---|---|
|  |  |  |  |

<!-- BLOCK_ID: WM-OPEN -->
## 5. Open / Alert / Assumption
- 사람 결정 필요:
- Source 재확인 필요:
- 현재 가정:
- Source Write를 제한하는 항목:

<!-- BLOCK_ID: WM-HITL-QUEUE -->
## 6. Human Decision Queue

> Agent가 작성·갱신하는 보류 질문 목록입니다. 사용자가 표를 직접 채우지 않습니다. `Recheck At`에 도달한 다음 Semantic Work에서 신규 질문보다 먼저 재확인합니다.

| Queue ID | 관련 Block | 질문 / 결정 필요사항 | 현재 확인값 / 제안 | 결정 담당 | 영향 분류 | Recheck At | 상태 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | SOURCE_BLOCK / ITERATE / ALERT |  | 미확정 / 확인중 / 제안 / 보류 / 확정 |

<!-- BLOCK_ID: WM-NEXT -->
## 7. 다음 작업
- 바로 수행할 Design/Development/Test Task:
- 다음 단계에서 재확인할 Queue:
- `/work`로 보완할 항목:
- `/change`가 필요한 의미 변경:
