from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from src.services.auth import (
    get_current_user_from_token
)

from src.services.face_embedding import (
    save_face_embedding_service,
    get_face_embedding_service,
    update_face_embedding_service,
    delete_face_embedding_service
)

from src.models.face_embedding import (
    CreateFaceEmbeddingRequest,
    FaceEmbeddingResponse
)

face_router = APIRouter(
    tags=["Face Embedding"]
)

bearer = HTTPBearer(auto_error=False)

@face_router.post(
    "/register",
    response_model=FaceEmbeddingResponse
)
def register_face(
    payload: CreateFaceEmbeddingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            401,
            "Not authenticated"
        )

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(
            401,
            "Invalid token"
        )

    face = save_face_embedding_service(
        str(user["_id"]),
        payload.embeddings
    )

    return FaceEmbeddingResponse(
        id=str(face["_id"]),
        user_id=str(face["user_id"]),
        embeddings=face["embeddings"],
        created_at=face["created_at"],
        updated_at=face.get("updated_at")
    )


@face_router.patch(
    "/me",
    response_model=FaceEmbeddingResponse
)
def update_face(
    payload: CreateFaceEmbeddingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            401,
            "Not authenticated"
        )

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(
            401,
            "Invalid token"
        )

    face = update_face_embedding_service(
        str(user["_id"]),
        payload.embeddings
    )

    if not face:
        raise HTTPException(
            404,
            "Face embedding not found"
        )

    return FaceEmbeddingResponse(
        id=str(face["_id"]),
        user_id=str(face["user_id"]),
        embeddings=face["embeddings"],
        created_at=face["created_at"],
        updated_at=face.get("updated_at")
    )


@face_router.get(
    "/me",
    response_model=FaceEmbeddingResponse
)
def get_my_face(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            401,
            "Not authenticated"
        )

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(
            401,
            "Invalid token"
        )

    face = get_face_embedding_service(
        str(user["_id"])
    )

    if not face:
        raise HTTPException(
            404,
            "Face embedding not found"
        )

    return FaceEmbeddingResponse(
        id=str(face["_id"]),
        user_id=str(face["user_id"]),
        embeddings=face["embeddings"],
        created_at=face["created_at"],
        updated_at=face.get("updated_at")
    )


@face_router.delete("/me")
def delete_my_face(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            401,
            "Not authenticated"
        )

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(
            401,
            "Invalid token"
        )

    deleted = delete_face_embedding_service(
        str(user["_id"])
    )

    if not deleted:
        raise HTTPException(
            404,
            "Face embedding not found"
        )

    return {
        "message": "Face embedding deleted successfully"
    }