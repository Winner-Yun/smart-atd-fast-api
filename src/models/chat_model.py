from pydantic import BaseModel

class CreateMessageRequest(BaseModel):
    message: str