# Program Spec

> Functional 의미는 Work Unit SDD를 참조하며 여기에서 반복 정의하지 않습니다. 이 문서는 실제 Source 구현 차이와 준비도를 연결하는 Engineering Projection입니다. 설계/Evidence 보완은 `/work`, 업무 의미·TO-BE 변경은 `/change`로 처리합니다.
>
> 모든 기술 항목을 항상 채우지 않습니다. **실제 변경 특성에 해당하는 조건부 구현 블록만 활성화**하고, 나머지는 제거합니다.
>
> **사용자는 이 Template의 빈칸을 직접 채우지 않습니다.** Agent가 관련 Source/표준/Canonical을 먼저 분석하고 필요한 사람 결정만 질문합니다. 수정 요청은 `이 문서의 [BLOCK:PGM-SOURCE-EVIDENCE]를 현재 Source 기준으로 다시 갱신해줘`처럼 Block을 지정합니다.

**Block ID:** `PGM-INTENT`, `PGM-TARGET`, `PGM-SOURCE-EVIDENCE`, `PGM-DELTA`, `PGM-CONDITIONAL`, `PGM-SOURCE-BOUNDARY`, `PGM-TRACE`, `PGM-READINESS`, `PGM-ASBUILT`

<!-- BLOCK_ID: PGM-INTENT -->
## 1. Functional Intent Reference
- Work Unit / Functional Spec:
- 관련 Rule / AC:
- Program이 담당하는 범위:
- Program이 담당하지 않는 범위:

<!-- BLOCK_ID: PGM-TARGET -->
## 2. Implementation Target
| PGM/TASK | Source/Symbol | Change Type | Responsibility | Target Confidence |
|---|---|---|---|---|
|  |  | ADD/MOD/DEL/VERIFY |  | HIGH/MEDIUM/LOW |

<!-- BLOCK_ID: PGM-SOURCE-EVIDENCE -->
## 3. Source Evidence
| Evidence | 위치/식별자 | 현재 동작 | 신뢰/상태 | 변경 관련성 |
|---|---|---|---|---|
|  |  |  | OBSERVED / CONFIRMED / OPEN |  |

- Call/Data/Interface 관계:
- 재생성 가능한 Query/Table/Symbol/Locator/Hash는 Machine Evidence로 관리:
- 확인하지 못한 Source/DB/Interface 영역:

<!-- BLOCK_ID: PGM-DELTA -->
## 4. Implementation Delta
- 바꿀 로직:
- 유지할 로직:
- 입력/출력 변화:
- Transaction / Exception / Logging 변화:

<!-- BLOCK_ID: PGM-CONDITIONAL -->
## 5. 조건부 구현 블록

> 아래 블록은 예시 분류다. Trigger가 없는 블록은 최종 문서에서 제거한다. Project Custom Template은 이 목록에 기술스택 고유 블록을 추가할 수 있다.

| Block | Trigger / Evidence | 설계해야 할 핵심 | 적용 여부 |
|---|---|---|---|
| UI / Interaction | 화면·사용자 동작 변경 | 입력/출력, Action, 상태, Validation | Y/N |
| Data Mapping | DTO/Form/Field 매핑 변경 | 필드 연결, Format, Validation | Y/N |
| Data Access / Schema | Query/Table/Column 영향 | CRUD, Join, Filter, Schema/Migration | Y/N |
| Transaction / Concurrency | 실행 경계·중복 위험 | Commit/Rollback, Lock, Idempotency | Y/N |
| Interface / Event | 외부 연계 영향 | Contract, Timeout, Retry, 실패 처리 | Y/N |
| Batch / Scheduler | 비동기·정기 실행 | 주기, 재실행, 중복 방지, 운영 통제 | Y/N |
| Security / Authorization | 권한·민감정보 영향 | 인증/인가, Data Scope, Masking/Audit | Y/N |
| DB Programmable Object | Procedure/Function/Trigger 영향 | 호출 계약, 내부 변경 경계, 배포 책임 | Y/N |
| NFR / Migration / Operation | 성능·운영·배포 영향 | SLA, Migration, Rollback, 관측 | Y/N |
| Architecture / Standard Deviation | 구조/표준 영향 | 적용 표준, 예외 이유, 승인/대안 | Y/N |

<!-- BLOCK_ID: PGM-SOURCE-BOUNDARY -->
## 6. Source Change Boundary

> Agent Source Write는 아래 목록에 포함된 대상 또는 명시적으로 승인된 추가 대상에 한정한다.

| Artifact / Source | 변경유형 | 변경 목적 | 실행 책임 | 허용 방식 | Evidence |
|---|---|---|---|---|---|
|  | ADD/MOD/DEL/VERIFY |  | DIRECT_MODIFY / SCRIPT_OUTPUT / HUMAN_OPERATION / VERIFY_ONLY |  |  |

### 실행 책임 의미
- `DIRECT_MODIFY`: Repository의 Source를 Agent가 직접 변경할 수 있다.
- `SCRIPT_OUTPUT`: Agent는 적용 스크립트/산출물을 만들고 실제 반영은 사람/운영자가 수행한다.
- `HUMAN_OPERATION`: 운영·관리도구·외부시스템에서 사람이 수행하며 Agent는 절차/검증 근거만 제공한다.
- `VERIFY_ONLY`: 변경하지 않고 영향/회귀만 검증한다.

<!-- BLOCK_ID: PGM-TRACE -->
## 7. TASK / AC / TC / Source
| TASK | AC | TC | Source | 상태 |
|---|---|---|---|---|
|  |  |  |  |  |

<!-- BLOCK_ID: PGM-READINESS -->
## 8. Implementation Readiness / Open Guard
| 항목 | 상태 | Evidence / 미확정 이유 | 실행 영향 |
|---|---|---|---|
| Functional Intent 기준 |  |  |  |
| 실제 구현 Target |  |  |  |
| Source Evidence / Coverage |  |  |  |
| Source Change Boundary |  |  |  |
| AC / TC 연결 |  |  |  |
| Security / Data / Operation Guard |  |  |  |

### Open 분류
| Open | 분류 | 제한되는 Source/Action | 해소 조건 | 상태 |
|---|---|---|---|---|
|  | SOURCE_BLOCK / ITERATE / ALERT |  |  | OPEN / CLOSED |

- Readiness: `READY / PARTIAL / EXECUTION_GUARDED`
- Source Write Guard:
- 필요한 추가 Evidence:

<!-- BLOCK_ID: PGM-ASBUILT -->
## 9. AS-BUILT Difference
- 실제 변경:
- Spec 대비 차이:
- 계획 밖 변경이 있었다면 이유와 승인/근거:
- Drift / Reconciliation 결과:
