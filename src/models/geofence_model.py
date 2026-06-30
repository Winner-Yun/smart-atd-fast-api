from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class UpdateGeofenceRequest(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None


class GeofenceResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    latitude: float
    longitude: float
    radius_meters: int
    created_at: datetime