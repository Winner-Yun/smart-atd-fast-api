from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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