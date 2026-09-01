package com.acme.attendance;

import java.time.LocalDate;
import org.apache.ibatis.annotations.Param;

public interface AttendanceCloseMapper {
    int selectPlannedMinutes(@Param("employeeId") String employeeId, @Param("workDate") LocalDate workDate);
    int isMonthClosed(@Param("employeeId") String employeeId, @Param("workDate") LocalDate workDate);
    int hasApprovedCorrection(@Param("employeeId") String employeeId, @Param("workDate") LocalDate workDate);
    int upsertDailyAttendance(@Param("employeeId") String employeeId, @Param("workDate") LocalDate workDate, @Param("reflectedMinutes") int reflectedMinutes);
    int updateCloseStatus(@Param("employeeId") String employeeId, @Param("workDate") LocalDate workDate, @Param("closeType") String closeType, @Param("status") String status);
}
