import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class TokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UpdateProfileRequest(BaseModel):
    name: str
    gender: Optional[str] = None

class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    google_id: str
    email: EmailStr
    name: str
    avatar: Optional[str] = None
    gender: Optional[str] = None
    provider: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        populate_by_name = True