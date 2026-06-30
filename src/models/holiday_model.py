from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

# =========================
# HOLIDAY CONFIG MODELS
# =========================
class UpdateHolidayConfigRequest(BaseModel):
    include_public_holidays: Optional[bool] = None
    include_weekend: Optional[Literal["Sunday only", "Saturday and Sunday", "None"]] = None

class HolidayConfigResponse(BaseModel):
    workspace_id: str
    include_public_holidays: bool
    include_weekend: str
    updated_at: datetime

# =========================
# CUSTOM HOLIDAY MODELS (Existing)
# =========================
class CreateHolidayRequest(BaseModel):
    name: str
    date: str

class UpdateHolidayRequest(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None

class HolidayResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    date: str
    created_at: datetime
    updated_at: Optional[datetime] = None