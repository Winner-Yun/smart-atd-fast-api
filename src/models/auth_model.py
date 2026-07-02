# src/models/auth_model.py
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class TokenRequest(BaseModel):
    token: str

# Updated to include the refresh token field
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

# Added for the refresh and logout endpoints
class RefreshTokenRequest(BaseModel):
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

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