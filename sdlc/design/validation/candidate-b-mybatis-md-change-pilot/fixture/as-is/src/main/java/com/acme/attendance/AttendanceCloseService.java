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
        int plannedMinutes = mapper.selectPlannedMinutes(employeeId, workDate);
        int reflectedMinutes = (plannedMinutes / 30) * 30;
        mapper.upsertDailyAttendance(employeeId, workDate, reflectedMinutes);
        mapper.updateCloseStatus(employeeId, workDate, closeType, "CLOSED");
    }
}
