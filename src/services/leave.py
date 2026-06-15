from bson import ObjectId
from datetime import datetime, timezone

from src.config.mongo import collections


def leave_col():
    return collections("leave_requests")


def member_col():
    return collections("workspace_members")


# =========================
# CREATE LEAVE REQUEST
# =========================
def create_leave_service(
    workspace_id: str,
    user_id: str,
    leave_type: str,
    reason: str,
    start_date: str,
    end_date: str
):

    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if not member:
        return "not_member"

    leave = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "leave_type": leave_type,
        "reason": reason,
        "start_date": start_date,
        "end_date": end_date,
        "status": "pending",
        "approved_by": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    result = leave_col().insert_one(leave)

    leave["_id"] = result.inserted_id

    return leave


# =========================
# GET MY LEAVES (with pagination)
# =========================
def get_my_leaves_service(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):

    skip = (page - 1) * limit
    direction = -1 if sort_order == "desc" else 1

    allowed = ["created_at", "start_date", "status"]
    if sort_by not in allowed:
        sort_by = "created_at"

    query = {"user_id": ObjectId(user_id)}

    leaves = list(
        leave_col()
        .find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(limit)
    )

    total = leave_col().count_documents(query)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "data": leaves
    }


# =========================
# GET WORKSPACE LEAVES (OWNER ONLY)
# =========================
def get_workspace_leaves_service(
    workspace_id: str,
    owner_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):

    owner = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(owner_id),
        "role": "owner"
    })

    if not owner:
        return "not_owner"

    skip = (page - 1) * limit
    direction = -1 if sort_order == "desc" else 1

    allowed = ["created_at", "start_date", "status"]
    if sort_by not in allowed:
        sort_by = "created_at"

    query = {"workspace_id": ObjectId(workspace_id)}

    leaves = list(
        leave_col()
        .find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(limit)
    )

    total = leave_col().count_documents(query)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "data": leaves
    }


# =========================
# UPDATE LEAVE
# ONLY OWNER OF LEAVE
# ONLY PENDING STATUS
# =========================
def update_leave_service(
    leave_id: str,
    user_id: str,
    leave_type: str | None,
    reason: str | None,
    start_date: str | None,
    end_date: str | None
):

    leave = leave_col().find_one({
        "_id": ObjectId(leave_id)
    })

    if not leave:
        return None

    if str(leave["user_id"]) != user_id:
        return "forbidden"

    if leave["status"] != "pending":
        return "not_allowed"

    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if leave_type is not None:
        update_data["leave_type"] = leave_type

    if reason is not None:
        update_data["reason"] = reason

    if start_date is not None:
        update_data["start_date"] = start_date

    if end_date is not None:
        update_data["end_date"] = end_date

    leave_col().update_one(
        {
            "_id": ObjectId(leave_id)
        },
        {
            "$set": update_data
        }
    )

    return leave_col().find_one({
        "_id": ObjectId(leave_id)
    })


# =========================
# APPROVE / REJECT LEAVE
# OWNER ONLY
# =========================
def approve_leave_service(
    leave_id: str,
    owner_id: str,
    status: str
):

    leave = leave_col().find_one({
        "_id": ObjectId(leave_id)
    })

    if not leave:
        return None

    owner = member_col().find_one({
        "workspace_id": leave["workspace_id"],
        "user_id": ObjectId(owner_id),
        "role": "owner"
    })

    if not owner:
        return "not_owner"

    if leave["status"] != "pending":
        return "already_processed"

    leave_col().update_one(
        {
            "_id": ObjectId(leave_id)
        },
        {
            "$set": {
                "status": status,
                "approved_by": ObjectId(owner_id),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return leave_col().find_one({
        "_id": ObjectId(leave_id)
    })


# =========================
# DELETE LEAVE
# ONLY OWNER OF LEAVE
# ONLY PENDING STATUS
# =========================
def delete_leave_service(
    leave_id: str,
    user_id: str
):

    leave = leave_col().find_one({
        "_id": ObjectId(leave_id)
    })

    if not leave:
        return None

    if str(leave["user_id"]) != user_id:
        return "forbidden"

    if leave["status"] != "pending":
        return "not_allowed"

    leave_col().delete_one({
        "_id": ObjectId(leave_id)
    })

    return leave