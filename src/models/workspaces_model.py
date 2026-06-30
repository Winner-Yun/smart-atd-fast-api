from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreateWorkspaceRequest(BaseModel):
    workspace_name: str = Field(..., example="ABC Company")
    description: Optional[str] = Field(None, example="Software Company")


class UpdateWorkspaceRequest(BaseModel):
    workspace_name: Optional[str] = Field(None, example="ABC Company")
    description: Optional[str] = Field(None, example="Software Company")
    status: Optional[str] = Field(None, example="active")


class AddMemberRequest(BaseModel):
    workspace_id: str
    user_id: str
    role: str = "employee"


class WorkspaceMemberResponse(BaseModel):
    workspace_id: str
    user_id: str
    role: str
    joined_at: datetime