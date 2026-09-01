package com.acme.attendance;

import java.time.LocalDate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AttendanceCloseService {
    private final AttendanceCloseMapper mapper;
    public AttendanceCloseService(AttendanceCloseMapper mapper) { this.mapper = mapper; }

    @Transactional
    public void closeDaily(String employeeId, LocalDate workDate, String closeType) {
        boolean monthClosed = mapper.isMonthClosed(employeeId, workDate) > 0;
        if (monthClosed) {
            boolean approved = mapper.hasApprovedCorrection(employeeId, workDate) > 0;
            if (!approved || "FORCE_CLOSE".equals(closeType)) {
                throw new IllegalStateException("월마감 이후 재집계 허용 조건을 충족하지 못했습니다.");
            }
        }
        int plannedMinutes = mapper.selectPlannedMinutes(employeeId, workDate);
        int reflectedMinutes = (plannedMinutes / 10) * 10;
        mapper.upsertDailyAttendance(employeeId, workDate, reflectedMinutes);
        mapper.updateCloseStatus(employeeId, workDate, closeType, "CLOSED");
    }
}
