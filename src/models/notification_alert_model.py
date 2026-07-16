from pydantic import BaseModel, Field

class CreateNotificationAlertRequest(BaseModel):
    title: str = Field(..., description="Alert subject/header")
    message: str = Field(..., description="Alert detail body")
    type: str = Field(..., description="Alert status category (e.g., present, late, absent, info)")

class NotificationAlertResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: str