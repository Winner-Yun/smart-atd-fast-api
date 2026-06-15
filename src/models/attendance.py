from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CheckInRequest(BaseModel):
    latitude: float
    longitude: float
    face_verified: bool
    liveness_verified: bool
    mock_location_detected: bool


class AttendanceResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str

    date: str

    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None

    status: str

    face_verified: bool
    liveness_verified: bool
    mock_location_detected: bool

    latitude: float
    longitude: float

    created_at: datetime
    updated_at: Optional[datetime] = None