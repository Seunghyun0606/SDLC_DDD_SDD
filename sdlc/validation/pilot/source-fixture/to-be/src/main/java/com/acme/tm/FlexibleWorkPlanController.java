package com.acme.tm;

public class FlexibleWorkPlanController {
    private final FlexibleWorkPlanService service;
    public FlexibleWorkPlanController(FlexibleWorkPlanService service) { this.service = service; }
    public Object getPlan(String employeeId, String periodId) { return service.getPlan(employeeId, periodId); }
    public void savePlan(String employeeId, String periodId, Object plan) { service.savePlan(employeeId, periodId, plan); }
    // SIMULATED_TECHNICAL_CHOICE: explicit endpoint for pilot testability; not confirmed business policy.
    public Object initializeFirstPlan(String employeeId, String periodId) { return service.initializeFirstPlan(employeeId, periodId); }
}
