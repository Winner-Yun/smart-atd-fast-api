from pydantic import BaseModel
from typing import Optional


class UpdateAttendancePolicyRequest(BaseModel):
    check_in_start: Optional[str] = None
    check_in_end: Optional[str] = None

    late_buffer_minutes: Optional[int] = None
    deadline_scan_minutes: Optional[int] = None

    annual_leave_limit: Optional[int] = None
    sick_leave_limit: Optional[int] = None


class AttendancePolicyResponse(BaseModel):
    id: str
    workspace_id: str

    check_in_start: str
    check_in_end: str

    late_buffer_minutes: int
    deadline_scan_minutes: int

    annual_leave_limit: int
    sick_leave_limit: int