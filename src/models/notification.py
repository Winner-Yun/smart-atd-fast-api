from pydantic import BaseModel, Field
from typing import Optional


class CreateNotificationRequest(BaseModel):
    title: str = Field(..., example="New Notification",)
    message: str = Field(..., example="This is a new notification", )
    type: str = Field(..., example="info", )
    target: str = Field(..., example="global")


class NotificationResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    message: str
    type: str
    target: str
    is_read: bool
    created_at: str