from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections

def workspace_col():
    return collections("workspaces")

def member_col():
    return collections("workspace_members")

def user_col():
    return collections("users")

def invite_col():
    return collections("workspace_invites")


def get_workspace_members_service(
    workspace_id: str,
    search: str | None = None,
    sort_order: str = "asc",
    include_pending: bool = False
):
    ws_object_id = ObjectId(workspace_id)
    
    # 1. Fetch Registered Members
    members_cursor = list(member_col().find({"workspace_id": ws_object_id}))
    user_ids = [m["user_id"] for m in members_cursor]
    
    # Fetch associated user details
    users_cursor = list(user_col().find({"_id": {"$in": user_ids}}))
    user_map = {str(u["_id"]): u for u in users_cursor}

    member_list = []
    
    for m in members_cursor:
        user_id_str = str(m["user_id"])
        user_data = user_map.get(user_id_str, {})
        
        member_list.append({
            "id": user_id_str,
            "email": user_data.get("email", ""),
            "name": user_data.get("name", "Unknown User"),
            "role": m.get("role", "member"),
            "status": m.get("status", "active"),
            "is_pending": False,
            "joined_at": m.get("joined_at")
        })

    # 2. Fetch Pending Invites (if requested)
    if include_pending:
        invites_cursor = list(invite_col().find({
            "workspace_id": ws_object_id, 
            "status": "pending"
        }))
        
        for inv in invites_cursor:
            member_list.append({
                "id": str(inv["_id"]),  # Return invite ID for pending users
                "email": inv.get("email", ""),
                "name": "Pending Invite",
                "role": inv.get("role", "member"),
                "status": "pending",
                "is_pending": True,
                "joined_at": inv.get("created_at")
            })

    # 3. Apply Search Filter (Name or Email)
    if search:
        search_lower = search.lower()
        member_list = [
            m for m in member_list 
            if search_lower in m["email"].lower() or search_lower in m["name"].lower()
        ]

    # 4. Apply Sorting (A-Z or Z-A)
    # Sorts primarily by Name, falls back to Email if Name is missing
    is_reverse = True if sort_order.lower() == "desc" else False
    member_list.sort(
        key=lambda x: (x["name"] if x["name"] != "Pending Invite" else x["email"]).lower(),
        reverse=is_reverse
    )

    return member_list


def update_member_status_service(workspace_id: str, user_id: str, status: str):
    """Suspend or reactivate a member."""
    result = member_col().update_one(
        {
            "workspace_id": ObjectId(workspace_id),
            "user_id": ObjectId(user_id),
            "role": {"$ne": "owner"} # Prevent suspending the owner
        },
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
    )
    
    return result.modified_count > 0


def remove_member_service(workspace_id: str, user_id: str):
    """Completely remove a member from the workspace."""
    result = member_col().delete_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "role": {"$ne": "owner"} # Prevent removing the owner
    })
    
    return result.deleted_count > 0