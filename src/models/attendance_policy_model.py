from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class CreateAttendancePolicyRequest(BaseModel):
    name: str
    work_start_time: str      # e.g., "08:00 AM"
    work_end_time: str        # e.g., "05:00 PM"
    check_in_start: str       # e.g., "07:30 AM"
    check_out_start: str      # e.g., "04:30 PM"
    late_buffer_minutes: int  # e.g., 15
    deadline_scan_minutes: int # e.g., 30
    annual_leave_limit: int   # e.g., 18
    sick_leave_limit: int     # e.g., 6
    status: Optional[str] = "inactive"

class UpdateAttendancePolicyRequest(BaseModel):
    name: Optional[str] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    check_in_start: Optional[str] = None
    check_out_start: Optional[str] = None
    late_buffer_minutes: Optional[int] = None
    deadline_scan_minutes: Optional[int] = None
    annual_leave_limit: Optional[int] = None
    sick_leave_limit: Optional[int] = None
    status: Optional[str] = None

class AttendancePolicyResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    work_start_time: str
    work_end_time: str
    check_in_start: str
    check_out_start: str
    late_buffer_minutes: int
    deadline_scan_minutes: int
    annual_leave_limit: int
    sick_leave_limit: int
    status: str
    created_at: datetime