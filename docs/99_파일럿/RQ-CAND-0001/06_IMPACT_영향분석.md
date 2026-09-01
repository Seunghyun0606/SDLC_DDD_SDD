# 06 IMPACT — 영향분석

## 문서 목적
`SIMULATED_SOURCE_FIXTURE` Source 후보를 실제 변경 후보와 확인 대상에 분류한다.

## 30초 요약
Service MODIFY HIGH, Mapper VERIFY_ONLY, Controller는 Trigger 정책에 따라 CANDIDATE, 두 Table은 READ/WRITE 영향으로 식별된다.

## Workflow
`Discovery Evidence → Technical Impact → Functional Impact → Business Impact`

## 입력/Evidence
| 대상 | Locator | Source Hash | Confidence | Status |
|---|---|---|---|---|
| FlexibleWorkPlanService | `as-is/...Service.java` | sha256:490fd18a0e8a006d71805e9675dfd0707b764bb63fdd3758a128d76f1313fab4 | HIGH | SIMULATED_TECHNICAL_CANDIDATE |
| FlexibleWorkPlanMapper | `as-is/...Mapper.xml` | sha256:080ef6f36e761984065d9e36b8127f7c58ab3de54156e17bb15be991c6153612 | HIGH | VERIFY_ONLY_CANDIDATE |
| FlexibleWorkPlanController | `as-is/...Controller.java` | sha256:9bdf4da5e5a0d54354cb437c04450095fe68590d7025285c6334ec5b71d6475c | MEDIUM | CHECK_REQUIRED |
| TB_TM_FLEX_PLAN | Mapper/schema | sha256:6004b749a4dc613e0a9c3781c03c0d08afd0ea1d7528a06fbc83577960b76b50 | HIGH | READ_WRITE_IMPACT |

## 본문
### Technical Impact
- Service: 자동 생성 orchestration 로직 필요 → MODIFY
- Mapper: 필요한 select/upsert가 fixture에 이미 존재 → VERIFY_ONLY
- Controller: Trigger 방식 미확정 → CHECK_REQUIRED

### Functional Impact
저장/조회 유지 + 최초 자동 생성 추가.

### Business Impact
“최초” 정의, overwrite/skip, 기본 스케줄 미존재 정책은 CHECK_REQUIRED.

## 미확정/Alert/Assumption
Technical HIGH가 Business HIGH를 의미하지 않는다.

## 관련 ID/Traceability
`FR-03 → IMP-PILOT-SVC → PGM-PILOT-001 candidate`

## 다음 작업
DESIGN에서 OPEN 정책을 명시한 목표 동작을 정의한다.
