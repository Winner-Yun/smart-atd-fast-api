from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def chat_col():
    return collections("chat_messages")


def read_col():
    return collections("chat_reads")


def member_col():
    return collections("workspace_members")


def check_member(workspace_id, user_id):
    return member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })


# =========================
# SEND MESSAGE
# =========================
def send_message(workspace_id, user_id, message):
    data = {
        "workspace_id": ObjectId(workspace_id),
        "sender_id": ObjectId(user_id),
        "message": message,
        "is_edited": False,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    res = chat_col().insert_one(data)
    data["_id"] = res.inserted_id
    return data


# =========================
# GET MESSAGES
# =========================
def get_messages(workspace_id, user_id):
    messages = chat_col().find({
        "workspace_id": ObjectId(workspace_id),
        "is_deleted": False
    }).sort("created_at", 1)

    result = []

    for m in messages:

        read = read_col().find_one({
            "message_id": m["_id"],
            "user_id": ObjectId(user_id)
        })

        result.append({
            "id": str(m["_id"]),
            "sender_id": str(m["sender_id"]),
            "message": m["message"],
            "is_edited": m.get("is_edited", False),
            "is_deleted": m.get("is_deleted", False),
            "is_read": True if read else False,
            "created_at": m["created_at"],
            "updated_at": m.get("updated_at")
        })

    return result


# =========================
# READ MESSAGE
# =========================
def read_message(workspace_id, message_id, user_id):
    if not check_member(workspace_id, user_id):
        return None

    exists = read_col().find_one({
        "message_id": ObjectId(message_id),
        "user_id": ObjectId(user_id)
    })

    if exists:
        return True

    read_col().insert_one({
        "message_id": ObjectId(message_id),
        "user_id": ObjectId(user_id),
        "read_at": datetime.now(timezone.utc)
    })

    return True


# =========================
# EDIT MESSAGE
# =========================
def edit_message(workspace_id, message_id, user_id, new_message):
    msg = chat_col().find_one({
        "_id": ObjectId(message_id),
        "workspace_id": ObjectId(workspace_id),
        "sender_id": ObjectId(user_id),
        "is_deleted": False
    })

    if not msg:
        return None

    chat_col().update_one(
        {"_id": ObjectId(message_id)},
        {
            "$set": {
                "message": new_message,
                "is_edited": True,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return chat_col().find_one({"_id": ObjectId(message_id)})


# =========================
# UNSEND (SOFT DELETE)
# =========================
def delete_message(workspace_id, message_id, user_id):
    msg = chat_col().find_one({
        "_id": ObjectId(message_id),
        "workspace_id": ObjectId(workspace_id),
        "sender_id": ObjectId(user_id),
        "is_deleted": False
    })

    if not msg:
        return None

    chat_col().update_one(
        {"_id": ObjectId(message_id)},
        {
            "$set": {
                "is_deleted": True,
                "message": "This message was deleted",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return True