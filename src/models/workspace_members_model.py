from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UpdateMemberStatusRequest(BaseModel):
    status: str


class WorkspaceMemberResponse(BaseModel):
    id: str
    google_id: Optional[str] = None
    email: Optional[EmailStr] = None
    name: str
    avatar: Optional[str] = None
    gender: Optional[str] = None
    provider: Optional[str] = None
    status: str

    role: str
    is_pending: bool
    joined_at: Optional[datetime] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "6868f6b5d0bcbcb6d89d1234",
                "google_id": "108123456789012345678",
                "email": "john@example.com",
                "name": "John Doe",
                "avatar": "https://lh3.googleusercontent.com/...",
                "gender": "male",
                "provider": "google",
                "status": "active",
                "role": "owner",
                "is_pending": False,
                "joined_at": "2026-07-05T08:30:00Z",
                "created_at": "2026-07-01T09:00:00Z",
                "updated_at": "2026-07-05T08:30:00Z"
            }
        }


class WorkspaceMemberListResponse(BaseModel):
    workspace_id: str
    total: int
    members: List[WorkspaceMemberResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_id": "6868f6b5d0bcbcb6d89d5678",
                "total": 1,
                "members": [
                    {
                        "id": "6868f6b5d0bcbcb6d89d1234",
                        "google_id": "108123456789012345678",
                        "email": "john@example.com",
                        "name": "John Doe",
                        "avatar": "https://lh3.googleusercontent.com/...",
                        "gender": "male",
                        "provider": "google",
                        "status": "active",
                        "role": "owner",
                        "is_pending": False,
                        "joined_at": "2026-07-05T08:30:00Z",
                        "created_at": "2026-07-01T09:00:00Z",
                        "updated_at": "2026-07-05T08:30:00Z"
                    }
                ]
            }
        }