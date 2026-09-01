# 05 DISCOVERY — Source Evidence

> 모든 Source 행은 `SIMULATED_SOURCE_FIXTURE`이며 실제 운영 시스템 Evidence가 아니다.

## 문서 목적
Static Analysis First 방식으로 관련 file/symbol/data 후보를 축소한다.

## 30초 요약
Controller→Service→Mapper→Table의 직접 relation을 fixture에서 관찰했다. 자동 생성 로직은 AS-IS Service에 존재하지 않는다.

## Workflow
`Requirement keyword → symbol/file candidate → direct call/data evidence → trace candidate`

## 입력/Evidence
| Artifact | Symbol/Relation | Truth/Evidence | Locator | Source Hash | Confidence | Status |
|---|---|---|---|---|---|---|
| Controller | getPlan/savePlan | SIMULATED_SOURCE_FIXTURE | `as-is/.../FlexibleWorkPlanController.java` | sha256:9bdf4da5e5a0d54354cb437c04450095fe68590d7025285c6334ec5b71d6475c | HIGH | OBSERVED |
| Service | getPlan/savePlan | SIMULATED_SOURCE_FIXTURE | `as-is/.../FlexibleWorkPlanService.java` | sha256:490fd18a0e8a006d71805e9675dfd0707b764bb63fdd3758a128d76f1313fab4 | HIGH | OBSERVED |
| Mapper | selectPlan/upsertPlan/selectDefaultSchedule | SIMULATED_SOURCE_FIXTURE | `as-is/.../FlexibleWorkPlanMapper.xml` | sha256:080ef6f36e761984065d9e36b8127f7c58ab3de54156e17bb15be991c6153612 | HIGH | OBSERVED |
| DATA | TB_TM_FLEX_PLAN / TB_TM_DEFAULT_SCHEDULE | SIMULATED_SOURCE_FIXTURE | Mapper SQL + schema.sql | sha256:6004b749a4dc613e0a9c3781c03c0d08afd0ea1d7528a06fbc83577960b76b50 | HIGH | OBSERVED |

## 본문
### Trace Candidate
`Controller → FlexibleWorkPlanService → FlexibleWorkPlanMapper → TB_TM_FLEX_PLAN / TB_TM_DEFAULT_SCHEDULE`

### Gap Observation
- `selectDefaultSchedule`는 존재하지만 AS-IS Service에서 호출되지 않는다.
- FR-03 구현 위치 후보는 Service HIGH, Mapper VERIFY_ONLY, Controller CANDIDATE다.

## 미확정/Alert/Assumption
Source relation은 기술 관찰이며 Business Rule로 확정하지 않는다.

## 관련 ID/Traceability
`FR-CAND-0001-01~03 ↔ ART-PILOT-CTL/SVC/MAP ↔ DATA-PILOT-PLAN/DEFAULT`

## 다음 작업
IMPACT에서 Technical/Functional/Business Impact를 분리한다.
