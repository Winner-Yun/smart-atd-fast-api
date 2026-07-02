import os
import json
from bson import ObjectId
from datetime import datetime, timezone
from cryptography.fernet import Fernet

from src.config.mongo import collections

ENCRYPTION_KEY = os.getenv("FACE_EMBEDDING_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("FACE_EMBEDDING_ENCRYPTION_KEY must be set in .env")

fernet = Fernet(ENCRYPTION_KEY)

def face_col():
    return collections("face_embeddings")

def _encrypt_vector(embeddings: list[float]) -> str:
    """Converts a float list to an encrypted string."""
    data = json.dumps(embeddings).encode('utf-8')
    return fernet.encrypt(data).decode('utf-8')

def _decrypt_vector(encrypted_data: str) -> list[float]:
    """Decrypts a string back to a float list."""
    decrypted_data = fernet.decrypt(encrypted_data.encode('utf-8'))
    return json.loads(decrypted_data.decode('utf-8'))

# =========================
# CREATE
# =========================
def save_face_embedding_service(
    user_id: str,
    embeddings: list[float]
):
    encrypted_embeddings = _encrypt_vector(embeddings)
    
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
                    "embeddings": encrypted_embeddings,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        updated = face_col().find_one({"user_id": ObjectId(user_id)})
        updated["embeddings"] = _decrypt_vector(updated["embeddings"])
        return updated

    face = {
        "user_id": ObjectId(user_id),
        "embeddings": encrypted_embeddings,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    result = face_col().insert_one(face)
    face["_id"] = result.inserted_id

    face["embeddings"] = _decrypt_vector(face["embeddings"])
    return face

# ========================= 
# UPDATE
# =========================
def update_face_embedding_service(
    user_id: str,
    embeddings: list[float]
):
    encrypted_embeddings = _encrypt_vector(embeddings)
    
    result = face_col().update_one(
        {
            "user_id": ObjectId(user_id)
        },
        {
            "$set": {
                "embeddings": encrypted_embeddings,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    if result.matched_count == 0:
        return None

    updated = face_col().find_one({"user_id": ObjectId(user_id)})
    updated["embeddings"] = _decrypt_vector(updated["embeddings"])
    return updated

# =========================
# GET MY FACE
# =========================
def get_face_embedding_service(
    user_id: str
):
    face = face_col().find_one({
        "user_id": ObjectId(user_id)
    })
    
    if face:
        face["embeddings"] = _decrypt_vector(face["embeddings"])
        
    return face


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