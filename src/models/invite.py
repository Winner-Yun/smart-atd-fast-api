from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class CreateInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="employee")
    expire_hours: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Invite expiration in hours"
    )


class InviteResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    expires_at: datetime