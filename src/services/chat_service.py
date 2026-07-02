from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


# ==============================================================================
# DATABASE ACCESSORS
# ==============================================================================

def chat_col():
    return collections("chat_messages")


def conversation_col():
    return collections("conversations")


def read_col():
    return collections("chat_reads")


def member_col():
    return collections("workspace_members")


def user_col():
    return collections("users")


def check_member(workspace_id: ObjectId, user_id: ObjectId) -> bool:
    member = member_col().find_one({
        "workspace_id": workspace_id,
        "user_id": user_id
    })
    return bool(member)


# ==============================================================================
# ROOM/CONVERSATION CORE SERVICES
# ==============================================================================

def get_or_create_conversation(user_id: str, workspace_id: str, payload: dict):
  
    u_id = ObjectId(user_id)
    w_id = ObjectId(workspace_id)
    conv_type = payload.get("type", "private")

    # Verify the current user belongs to the requested workspace
    if not check_member(w_id, u_id):
        return None, "Access denied. You are not a member of this workspace."

    if conv_type == "private":
        receiver_email = payload.get("receiver_email")
        if not receiver_email:
            return None, "A receiver email is required to initialize a private chat room."

        # Find target user via email lookup
        receiver = user_col().find_one({"email": receiver_email})
        if not receiver:
            return None, f"No user account found matching email: {receiver_email}"

        r_id = receiver["_id"]

        if u_id == r_id:
            return None, "You cannot establish a private conversation room with yourself."

      
        if not check_member(w_id, r_id):
            return None, "The target recipient user is not a member of this workspace."

      
        query = {
            "workspace_id": w_id,
            "type": "private",
            "participants": {"$all": [u_id, r_id], "$size": 2}
        }
        conv = conversation_col().find_one(query)

        if not conv:
            new_conv = {
                "workspace_id": w_id,
                "type": "private",
                "participants": [u_id, r_id],
                "created_at": datetime.now(timezone.utc),
                "last_message": None
            }
            res = conversation_col().insert_one(new_conv)
            new_conv["_id"] = res.inserted_id
            return new_conv, None

        return conv, None

    else:
        
        name = payload.get("workspace_name", "Unnamed Channel")
        p_ids = [ObjectId(pid) for pid in payload.get("participant_ids", [])]

        if u_id not in p_ids:
            p_ids.append(u_id)

      
        valid_participants = [pid for pid in p_ids if check_member(w_id, pid)]

        new_group = {
            "workspace_id": w_id,
            "type": "group",
            "name": name,
            "participants": valid_participants,
            "created_at": datetime.now(timezone.utc),
            "last_message": None
        }
        res = conversation_col().insert_one(new_group)
        new_group["_id"] = res.inserted_id
        return new_group, None


def get_user_conversations(user_id: str, workspace_id: str) -> list:
    
    query = {
        "workspace_id": ObjectId(workspace_id),
        "participants": ObjectId(user_id)
    }
    cursor = conversation_col().find(query).sort("last_message.created_at", -1)

    result = []
    for c in cursor:
        last_msg = c.get("last_message")
        if last_msg and isinstance(last_msg.get("created_at"), datetime):
            last_msg["created_at"] = last_msg["created_at"].isoformat()

        result.append({
            "id": str(c["_id"]),
            "workspace_id": str(c["workspace_id"]),
            "type": c["type"],
            "name": c.get("name", "Direct Message"),
            "participants": [str(p) for p in c["participants"]],
            "created_at": c["created_at"].isoformat() if isinstance(c["created_at"], datetime) else c["created_at"],
            "last_message": last_msg
        })
    return result


# ==============================================================================
# MESSAGING OPERATIONS
# ==============================================================================

def save_new_message(conversation_id: str, workspace_id: str, sender_id: str, message_text: str) -> dict:
  
    c_id = ObjectId(conversation_id)
    w_id = ObjectId(workspace_id)
    s_id = ObjectId(sender_id)

    # Cross-reference that conversation, workspace, and sender match up safely
    conv = conversation_col().find_one({
        "_id": c_id, 
        "workspace_id": w_id, 
        "participants": s_id
    })
    if not conv:
        return None

    msg_data = {
        "conversation_id": c_id,
        "workspace_id": w_id,
        "sender_id": s_id,
        "message": message_text,
        "is_edited": False,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    res = chat_col().insert_one(msg_data)
    msg_data["_id"] = res.inserted_id

   
    conversation_col().update_one(
        {"_id": c_id},
        {"$set": {
            "last_message": {
                "message_id": str(msg_data["_id"]),
                "message": message_text,
                "sender_id": str(sender_id),
                "created_at": msg_data["created_at"]
            }
        }}
    )
    return msg_data


def get_messages_by_conversation(conversation_id: str, workspace_id: str, user_id: str) -> list:
  
    c_id = ObjectId(conversation_id)
    w_id = ObjectId(workspace_id)
    u_id = ObjectId(user_id)

    if not conversation_col().find_one({"_id": c_id, "workspace_id": w_id, "participants": u_id}):
        return None

    messages = chat_col().find({"conversation_id": c_id}).sort("created_at", 1)
    result = []

    for m in messages:
        has_read = read_col().find_one({"message_id": m["_id"], "user_id": u_id})

        result.append({
            "id": str(m["_id"]),
            "conversation_id": str(m["conversation_id"]),
            "sender_id": str(m["sender_id"]),
            "message": "[This message was deleted]" if m.get("is_deleted", False) else m["message"],
            "is_edited": m.get("is_edited", False),
            "is_deleted": m.get("is_deleted", False),
            "is_read": True if has_read else False,
            "created_at": m["created_at"].isoformat() if isinstance(m["created_at"], datetime) else m["created_at"],
            "updated_at": m.get("updated_at").isoformat() if isinstance(m.get("updated_at"), datetime) else None
        })
    return result


def modify_message_text(message_id: str, workspace_id: str, user_id: str, new_text: str) -> dict:
    m_id = ObjectId(message_id)
    w_id = ObjectId(workspace_id)
    u_id = ObjectId(user_id)

    msg = chat_col().find_one({"_id": m_id, "workspace_id": w_id, "sender_id": u_id, "is_deleted": False})
    if not msg:
        return None

    chat_col().update_one(
        {"_id": m_id},
        {"$set": {
            "message": new_text,
            "is_edited": True,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    return chat_col().find_one({"_id": m_id})


def soft_delete_message(message_id: str, workspace_id: str, user_id: str) -> bool:
    m_id = ObjectId(message_id)
    w_id = ObjectId(workspace_id)
    u_id = ObjectId(user_id)

    msg = chat_col().find_one({"_id": m_id, "workspace_id": w_id, "sender_id": u_id, "is_deleted": False})
    if not msg:
        return False

    chat_col().update_one(
        {"_id": m_id},
        {"$set": {
            "is_deleted": True,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    return True


def mark_message_as_read(message_id: str, user_id: str) -> bool:
    m_id = ObjectId(message_id)
    u_id = ObjectId(user_id)

    msg = chat_col().find_one({"_id": m_id})
    if not msg:
        return False

    exists = read_col().find_one({"message_id": m_id, "user_id": u_id})
    if exists:
        return True

    read_col().insert_one({
        "message_id": m_id,
        "user_id": u_id,
        "read_at": datetime.now(timezone.utc)
    })
    return True