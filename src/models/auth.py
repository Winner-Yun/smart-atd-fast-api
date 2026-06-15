from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., example="winner@gmail.com")
    password: str = Field(..., min_length=8, example="Password123")
    first_name: str = Field(..., example="Winner")
    last_name: str = Field(..., example="Yun")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="winner@gmail.com")
    password: str = Field(..., example="Password123")


class UpdateProfileRequest(BaseModel):
    first_name: str = Field(..., example="Winner")
    last_name: str = Field(..., example="Yun")
    gender: Optional[str] = Field(None, example="Male")
    status: str = Field(default="active", example="active")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    gender: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    

class SignUpResponse(UserResponse):
    access_token: str
    token_type: str = "bearer"
