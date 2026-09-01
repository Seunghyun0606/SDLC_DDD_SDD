# Minimal Filled Example

## 고객 입력
Requirement:
- 10분 단위 근무계획 등록
- 근무계획 수정
- Calendar 조회

SoP:
- Who: ESS 탄력근로제 근무자
- When: 매일
- Where: ESS 근무계획 메뉴
- What: 일자/시작/종료
- How: 10분 단위 저장
- Why: 근태집계/마감 기준 제공

## 6W
ESS 탄력근로제 근무자가 매일 ESS 근무계획 메뉴에서 근무일자/시작/종료시간을 10분 단위로 검증하여 저장/수정한다. 목적은 근태집계/마감 기준 제공이다.

## Brownfield 분석
```text
flexWorkPlan.jsp
→ FlexWorkPlanController
→ FlexWorkPlanService.savePlan
→ FlexWorkPlanMapper
→ FlexWorkPlanMapper.xml
→ TB_FLEX_WORK_PLAN
```

AS-IS:
- UI 30분 option
- Service `%30`

TO-BE:
- UI 10분 option
- Service `%10`
- actual Confirmed Code는 OPEN

## 결과
- Customer Spec: 생성 가능
- Development Blueprint: 생성 가능
- Patch Proposal: 생성 가능
- Actual Source Write: 공통코드/권한/revision 확인 전 `PROPOSAL_ONLY`
