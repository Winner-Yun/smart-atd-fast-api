from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional


class CreateFaceEmbeddingRequest(BaseModel):
    embeddings: List[float]

    @field_validator("embeddings")
    @classmethod
    def validate_embedding_length(cls, v):
        if len(v) != 192:
            raise ValueError("Embedding must contain exactly 192 values")
        return v


class FaceEmbeddingResponse(BaseModel):
    id: str
    user_id: str
    embeddings: List[float]
    created_at: datetime
    updated_at: Optional[datetime] = None