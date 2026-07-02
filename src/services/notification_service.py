from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def notification_col():
    return collections("notifications")

def notification_read_col():
    return collections("notification_reads")

def member_col():
    return collections("workspace_members")

def user_col():
    return collections("users") 

def is_member(workspace_id: str, user_id: str):
    return member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

def create_notification_service(
    workspace_id: str,
    sender_id: str,
    title: str,
    message: str,
    type: str,
    target: str
):
  
    if target.startswith("personal:"):
        email = target.split(":")[1].strip()
        
        target_user = user_col().find_one({"email": email})
        if not target_user:
            return "user_not_found"
            
        target_user_id = str(target_user["_id"])
        
   
        if not is_member(workspace_id, target_user_id):
            return "not_member"
            
        target = f"personal:{target_user_id}"

    data = {
        "workspace_id": ObjectId(workspace_id),
        "sender_id": ObjectId(sender_id),
        "title": title,
        "message": message,
        "type": type,
        "target": target,
        "created_at": datetime.now(timezone.utc)
    }

    res = notification_col().insert_one(data)
    data["_id"] = res.inserted_id
    return data


def get_my_notifications_service(workspace_id: str, user_id: str):

    notifications = notification_col().find({
        "workspace_id": ObjectId(workspace_id),
        "$or": [
            {"target": "global"},
            {
                "target": {"$regex": "^personal:"},
            }
        ]
    }).sort("created_at", -1)

    result = []

    for n in notifications:

        target = n["target"]

        # personal check
        if target.startswith("personal:"):
            target_user = target.split(":")[1]
            if target_user != user_id:
                continue

        read = notification_read_col().find_one({
            "notification_id": n["_id"],
            "user_id": ObjectId(user_id)
        })

        result.append({
            "id": str(n["_id"]),
            "workspace_id": str(n["workspace_id"]),
            "title": n["title"],
            "message": n["message"],
            "type": n["type"],
            "target": n["target"],
            "is_read": bool(read),
            "created_at": str(n["created_at"])
        })

    return result


def read_notification_service(notification_id: str, user_id: str):

    n = notification_col().find_one({"_id": ObjectId(notification_id)})

    if not n:
        return None

    workspace_id = str(n["workspace_id"])
    target = n["target"]

    if not is_member(workspace_id, user_id):
        return "not_member"

    if target.startswith("personal:"):
        target_user = target.split(":")[1]

        if target_user != user_id:
            return "forbidden"

    exists = notification_read_col().find_one({
        "notification_id": ObjectId(notification_id),
        "user_id": ObjectId(user_id)
    })

    if not exists:
        notification_read_col().insert_one({
            "notification_id": ObjectId(notification_id),
            "user_id": ObjectId(user_id),
            "read_at": datetime.now(timezone.utc)
        })

    return True