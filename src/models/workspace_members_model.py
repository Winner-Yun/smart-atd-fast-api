from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UpdateMemberStatusRequest(BaseModel):
    status: str  

class WorkspaceMemberResponse(BaseModel):
    id: str 
    email: EmailStr
    name: str
    role: str
    status: str
    is_pending: bool
    joined_at: Optional[datetime] = None

class WorkspaceMemberListResponse(BaseModel):
    workspace_id: str
    total: int
    members: List[WorkspaceMemberResponse]