# Work Unit SDD

> 이 문서는 Canonical Spec 기반의 개발/설계용 Living Spec입니다. 사람이 일반 제출문서처럼 별도 원장으로 유지하지 않습니다. 오탈자만 직접 수정하고, 설계/Evidence 보완은 `/work`, 업무 의미·정책·TO-BE 동작 변경은 `/change`로 처리합니다.
>
> 이 문서는 **업무 의미를 다시 만드는 문서가 아니라**, 개발자가 변경 경계·근거·목표 동작·검증 조건을 한 화면에서 확인하는 Engineering Projection입니다.
>
> **사용자는 이 Template의 빈칸을 처음부터 작성하지 않습니다.** Agent가 Canonical/Source를 먼저 분석해 초안을 만들고, 사람 결정이 필요한 Gap만 질문합니다. 수정 요청은 `이 문서의 [BLOCK:WU-BUSINESS-RULE]을 ...로 바꿔줘`처럼 Block을 지정합니다. 즉시 답할 수 없는 질문은 Agent가 `WU-HITL-QUEUE`에 남기고 `Recheck At`에서 다시 확인합니다.

**Block ID:** `WU-INTENT`, `WU-ASIS`, `WU-TOBE`, `WU-BUSINESS-RULE`, `WU-IMPACT`, `WU-MAPPING`, `WU-TECH-IMPACT`, `WU-DEV-CONTRACT`, `WU-AC-TEST`, `WU-OPEN-GUARD`, `WU-HITL-QUEUE`, `WU-ASBUILT`, `WU-VERIFY`

<!-- BLOCK_ID: WU-INTENT -->
## 1. 목적 / Functional Intent
- 이 Work Unit이 해결하는 문제:
- 사용자가 얻어야 하는 결과:
- 유지 조건:

### 1.1 Work Unit 경계
| 포함 범위 | 제외 범위 | 분할/결합 근거 | 독립 검증·배포 관점 |
|---|---|---|---|
|  |  |  |  |

> Work Unit은 화면 수나 CRUD 수가 아니라 함께 변경·검증되는 업무/기능 경계를 기준으로 한다. 구현 Program은 1:N일 수 있다.

<!-- BLOCK_ID: WU-ASIS -->
## 2. AS-IS Evidence / Coverage Gap
| Evidence | 구분 | 위치/식별자 | 관찰 내용 | 신뢰/상태 |
|---|---|---|---|---|
|  | Source/DB/UI/문서/Runtime |  |  | OBSERVED / CONFIRMED / OPEN |

### Coverage Gap
| Gap | 미확인 영역 | 왜 미확인인가 | 확인 방법 | 영향 | 상태 |
|---|---|---|---|---|---|
|  |  |  |  |  | OPEN / CLOSED |

> 확인하지 못한 영역을 임의로 `영향 없음`으로 바꾸지 않는다.

<!-- BLOCK_ID: WU-TOBE -->
## 3. TO-BE Spec
- 목표 동작:

### 3.1 Scenario / Flow
| Scenario | Actor / Trigger | 정상 흐름·종료조건 | 대안/예외 | 관련 Rule/AC |
|---|---|---|---|---|
|  |  |  |  |  |

- Validation / 상태 / 예외:
- 변경되지 않아야 하는 동작:

<!-- BLOCK_ID: WU-BUSINESS-RULE -->
## 4. Business Rule / Decision
| Rule/Decision | 상태 | 근거 | 영향 |
|---|---|---|---|
|  | CONFIRMED / OPEN |  |  |

<!-- BLOCK_ID: WU-IMPACT -->
## 5. 영향 범위
- Business / Functional Impact:
- Technical Impact:
- 변경되지 않는 범위:

<!-- BLOCK_ID: WU-MAPPING -->
## 6. 구현 Mapping
| TASK | PGM | Source/Symbol | 변경 유형 | 책임/역할 | 상태 |
|---|---|---|---|---|---|
|  |  |  | ADD/MOD/DEL/VERIFY |  |  |

<!-- BLOCK_ID: WU-TECH-IMPACT -->
## 7. Program / Data / Interface / Authorization 영향
- Program 책임 변화:
- Data/Table/Column 영향:
- Interface/Batch/Transaction 영향:
- 인증/인가·Data Scope 영향:

<!-- BLOCK_ID: WU-DEV-CONTRACT -->
## 8. Development Contract
- 구현 순서:
- 적용 표준 / Deviation:
- Source Write 허용 경계:
- 예상 밖 영향 발견 시 처리:

<!-- BLOCK_ID: WU-AC-TEST -->
## 9. AC / Test
| AC | TC/Scenario | Evidence | Result |
|---|---|---|---|
|  |  |  |  |

<!-- BLOCK_ID: WU-OPEN-GUARD -->
## 10. Open / Risk / Execution Guard
| Open/Risk | 분류 | Source Write 영향 | 담당 | 상태 |
|---|---|---|---|---|
|  | SOURCE_BLOCK / ITERATE / ALERT |  |  | OPEN / CLOSED |

### 분류 원칙
- `SOURCE_BLOCK`: 대상/범위, 핵심 동작, 보안·권한, 데이터 변경, 위험한 실행 조건이 불확실해 **해당 Source Write만 제한**한다. Stage 전체 진행을 자동 중단시키는 의미는 아니다.
- `ITERATE`: 대상과 큰 방향은 확정되어 구현 후 세부 조정이 가능한 항목이다.
- `ALERT`: 추적은 필요하지만 현재 구현을 제한하지 않는 확인/주의 항목이다.
- Framework의 Hard Block 정책과 충돌하면 Hard Block이 우선한다.

<!-- BLOCK_ID: WU-HITL-QUEUE -->
## 11. Human Decision Queue

> 사용자가 바로 답하지 못한 HITL 질문을 Agent가 기록·갱신합니다. 같은 질문은 단계가 바뀌어도 같은 Queue ID를 유지하며, `Recheck At`에 도달하면 다음 Agent가 신규 질문보다 먼저 재확인합니다. 이 표는 Canonical SSOT가 아니라 OPEN/DEFERRED의 Human View입니다.

| Queue ID | 관련 Block | 질문 / 결정 필요사항 | 현재 확인값 / 제안 | 결정 담당 | 영향 분류 | Recheck At | 상태 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  | SOURCE_BLOCK / ITERATE / ALERT | NEXT_SEMANTIC_WORK / BEFORE_SOURCE_WRITE / BEFORE_TEST / BEFORE_VERIFY / Stage | 미확정 / 확인중 / 제안 / 보류 / 확정 |

<!-- BLOCK_ID: WU-ASBUILT -->
## 12. AS-BUILT
- 실제 구현 결과:
- 설계 대비 차이:
- Source-derived 기술 정보:
- 추가로 발견된 영향:

<!-- BLOCK_ID: WU-VERIFY -->
## 13. Verification
- Build/Test/Regression:
- Canonical과 Source Drift 여부:
- Coverage Gap 해소 여부:
- 미해결 Human Decision Queue와 다음 Recheck At:
- 최종 판정 및 남은 작업:
