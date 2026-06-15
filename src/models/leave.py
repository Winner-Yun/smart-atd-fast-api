from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CreateLeaveRequest(BaseModel):
    leave_type: str
    reason: str
    start_date: str
    end_date: str


class UpdateLeaveRequest(BaseModel):
    leave_type: Optional[str] = None
    reason: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LeaveApprovalRequest(BaseModel):
    status: str  # approved or rejected


class LeaveResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    leave_type: str
    reason: str
    start_date: str
    end_date: str
    status: str
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None