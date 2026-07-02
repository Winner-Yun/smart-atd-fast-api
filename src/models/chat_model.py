from pydantic import BaseModel, Field
from typing import Optional, List


class CreateConversationRequest(BaseModel):
    type: str = Field(..., example="private OR group")
    receiver_email: Optional[str] = Field(None, example="user@example.com (Provide only if type is private)")
    workspace_name: Optional[str] = Field(None, example="Engineering Channel (Provide only if type is group)")
    participant_ids: Optional[List[str]] = Field(None, example=["id_1", "id_2 (Optional list for group channels)"])


class CreateMessageRequest(BaseModel):
    message: str = Field(..., example="Write your real-time chat message text here")


class EditMessageRequest(BaseModel):
    new_message: str = Field(..., example="Write your updated chat message text here")

