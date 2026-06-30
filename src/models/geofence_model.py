from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class CreateGeofenceRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    status: Optional[str] = "inactive"  # Defaults to inactive unless specified


class UpdateGeofenceRequest(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None
    status: Optional[str] = None  # Allows manual toggle or activation


class GeofenceResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    status: str  # Tracks "active" or "inactive" status
    created_at: datetime