from bson import ObjectId
from datetime import datetime, timezone

from src.config.mongo import collections


def face_col():
    return collections("face_embeddings")


# =========================
# CREATE
# =========================
def save_face_embedding_service(
    user_id: str,
    embeddings: list[float]
):
    existing = face_col().find_one({
        "user_id": ObjectId(user_id)
    })

    if existing:
        face_col().update_one(
            {
                "user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    "embeddings": embeddings,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        return face_col().find_one({
            "user_id": ObjectId(user_id)
        })

    face = {
        "user_id": ObjectId(user_id),
        "embeddings": embeddings,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    result = face_col().insert_one(face)

    face["_id"] = result.inserted_id

    return face

# ========================= 
# UPDATE
# =========================
def update_face_embedding_service(
    user_id: str,
    embeddings: list[float]
):
    result = face_col().update_one(
        {
            "user_id": ObjectId(user_id)
        },
        {
            "$set": {
                "embeddings": embeddings,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    return face_col().find_one({
        "user_id": ObjectId(user_id)
    })

# =========================
# GET MY FACE
# =========================
def get_face_embedding_service(
    user_id: str
):
    return face_col().find_one({
        "user_id": ObjectId(user_id)
    })


# =========================
# DELETE MY FACE
# =========================
def delete_face_embedding_service(
    user_id: str
):
    result = face_col().delete_one({
        "user_id": ObjectId(user_id)
    })

    return result.deleted_count > 0