from bson import ObjectId
from datetime import datetime, timezone, timedelta

from src.config.mongo import collections
from src.services.auth_service import get_user_by_email


def invite_col():
    return collections("workspace_invites")


def member_col():
    return collections("workspace_members")


def create_invite_service(
    workspace_id: str,
    email: str,
    role: str,
    expire_hours: int = 24
):
    user = get_user_by_email(email)

    if not user:
        return None

    existing = invite_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": user["_id"],
        "status": "pending"
    })

    if existing:
        return "already_invited"

    invite = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": user["_id"],
        "email": email,
        "role": role,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=expire_hours)
    }

    result = invite_col().insert_one(invite)
    invite["_id"] = result.inserted_id

    return invite


def accept_invite_service(
    invite_id: str,
    current_user_id: str
):
    invite = invite_col().find_one({
        "_id": ObjectId(invite_id)
    })

    if not invite:
        return None

    if str(invite["user_id"]) != current_user_id:
        return "forbidden"

    now = datetime.now(timezone.utc)

    expires_at = invite.get("expires_at")

    if expires_at:
        # MongoDB may return naive datetime
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            invite_col().update_one(
                {"_id": invite["_id"]},
                {
                    "$set": {
                        "status": "expired"
                    }
                }
            )

            return "expired"

    if invite["status"] != "pending":
        return "already_processed"

    existing_member = member_col().find_one({
        "workspace_id": invite["workspace_id"],
        "user_id": invite["user_id"]
    })

    if existing_member:
        return "already_member"

    member = {
        "workspace_id": invite["workspace_id"],
        "user_id": invite["user_id"],
        "role": invite["role"],
        "joined_at": datetime.now(timezone.utc)
    }

    member_col().insert_one(member)

    invite_col().update_one(
        {"_id": invite["_id"]},
        {
            "$set": {
                "status": "accepted",
                "accepted_at": datetime.now(timezone.utc)
            }
        }
    )

    return member

def get_workspace_invites_service(
    workspace_id: str,
    page: int = 1,
    limit: int = 10
):
    skip = (page - 1) * limit

    invites = list(
        invite_col()
        .find({
            "workspace_id": ObjectId(workspace_id)
        })
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total = invite_col().count_documents({
        "workspace_id": ObjectId(workspace_id)
    })

    data = []

    for invite in invites:
        data.append({
            "id": str(invite["_id"]),
            "workspace_id": str(invite["workspace_id"]),
            "user_id": str(invite["user_id"]),
            "email": invite["email"],
            "role": invite["role"],
            "status": invite["status"],
            "created_at": invite["created_at"],
            "expires_at": invite.get("expires_at")
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": data
    }

def delete_invite_service(invite_id: str, user_id: str):
    invite = invite_col().find_one({"_id": ObjectId(invite_id)})
    if not invite:
        return None

    member = member_col().find_one({
        "workspace_id": invite["workspace_id"],
        "user_id": ObjectId(user_id),
        "role": "owner"
    })

    if not member:
        return "not_owner"

    invite_col().delete_one({"_id": invite["_id"]})
    return True

def reject_invite_service(invite_id: str, user_id: str):
    invite = invite_col().find_one({"_id": ObjectId(invite_id)})
    if not invite:
        return None

    if str(invite["user_id"]) != user_id:
        return "forbidden"

    if invite["status"] != "pending":
        return "already_processed"

    invite_col().update_one(
        {"_id": invite["_id"]},
        {"$set": {"status": "rejected"}}
    )

    return True

def get_my_invites_service(user_id: str, page: int = 1, limit: int = 10):
    skip = (page - 1) * limit

    invites = list(
        invite_col()
        .find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total = invite_col().count_documents({"user_id": ObjectId(user_id)})

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": [
            {
                "id": str(i["_id"]),
                "workspace_id": str(i["workspace_id"]),
                "email": i["email"],
                "role": i["role"],
                "status": i["status"],
                "created_at": i["created_at"],
                "expires_at": i.get("expires_at")
            }
            for i in invites
        ]
    }