from datetime import datetime, timezone, timedelta
from bson import ObjectId
from src.config.mongo import collections

# Define the UTC+7 Local Timezone
LOCAL_TZ = timezone(timedelta(hours=7))

def alert_col():
    return collections("notification_alerts")

def member_col():
    return collections("workspace_members")

def is_member(workspace_id: str, user_id: str) -> bool:
    """Check if a user belongs to a workspace."""
    if not ObjectId.is_valid(workspace_id) or not ObjectId.is_valid(user_id):
        return False
    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })
    return bool(member)

def create_alert_service(workspace_id: str, user_id: str, title: str, message: str, type: str):
    if not ObjectId.is_valid(workspace_id) or not ObjectId.is_valid(user_id):
        return None

    if not is_member(workspace_id, user_id):
        return "not_member"

    data = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "title": title,
        "message": message,
        "type": type,
        "is_read": False,
        "created_at": datetime.now(LOCAL_TZ)
    }

    res = alert_col().insert_one(data)
    data["_id"] = res.inserted_id
    return data

def get_alerts_service(workspace_id: str, user_id: str):
    if not is_member(workspace_id, user_id):
        return "not_member"

    cursor = alert_col().find({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    }).sort("created_at", -1)

    result = []
    for doc in cursor:
        result.append({
            "id": str(doc["_id"]),
            "workspace_id": str(doc["workspace_id"]),
            "user_id": str(doc["user_id"]),
            "title": doc["title"],
            "message": doc["message"],
            "type": doc["type"],
            "is_read": doc.get("is_read", False),
            "created_at": str(doc["created_at"])
        })
    return result

def read_alert_service(workspace_id: str, alert_id: str, user_id: str):
    if not ObjectId.is_valid(alert_id) or not is_member(workspace_id, user_id):
        return "not_member"

    result = alert_col().update_one(
        {
            "_id": ObjectId(alert_id),
            "workspace_id": ObjectId(workspace_id),
            "user_id": ObjectId(user_id)
        },
        {"$set": {"is_read": True} , "$currentDate": {"updated_at": True}}
    )

    if result.matched_count == 0:
        return None

    return True

def delete_alert_service(workspace_id: str, alert_id: str, user_id: str):
    if not ObjectId.is_valid(alert_id) or not is_member(workspace_id, user_id):
        return "not_member"

    result = alert_col().delete_one({
        "_id": ObjectId(alert_id),
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 0:
        return None

    return True