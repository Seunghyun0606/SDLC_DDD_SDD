package com.acme.tm;

public class FlexibleWorkPlanService {
    private final FlexibleWorkPlanMapper mapper;
    public FlexibleWorkPlanService(FlexibleWorkPlanMapper mapper) { this.mapper = mapper; }
    public Object getPlan(String employeeId, String periodId) { return mapper.selectPlan(employeeId, periodId); }
    public void savePlan(String employeeId, String periodId, Object plan) { mapper.upsertPlan(employeeId, periodId, plan); }
}
