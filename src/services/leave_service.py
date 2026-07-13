from bson import ObjectId
from datetime import datetime, timedelta, timezone

from src.services.workspaces_service import attendance_col
from src.config.mongo import collections


def leave_col():
    return collections("leave_requests")


def member_col():
    return collections("workspace_members")


def _parse_leave_date(date_value):
    if isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.fromisoformat(date_value)
            except ValueError:
                return None

    return None


def _validate_leave_dates(start_date, end_date):
    start_dt = _parse_leave_date(start_date)
    end_dt = _parse_leave_date(end_date)

    if not start_dt or not end_dt:
        return None, None, "invalid_leave_dates"

    if start_dt.date() > end_dt.date():
        return None, None, "invalid_leave_range"

    return start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"), None


# =========================
# HELPER: SERIALIZE OBJECTID
# =========================
def serialize_mongo_doc(doc):
    """
    Recursively converts MongoDB ObjectIds to strings in dictionaries and lists.
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, (dict, list)):
                doc[key] = serialize_mongo_doc(value)
    return doc


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

    start_date_value, end_date_value, error = _validate_leave_dates(start_date, end_date)
    if error:
        return error

    leave = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "leave_type": leave_type,
        "reason": reason,
        "start_date": start_date_value,
        "end_date": end_date_value,
        "status": "pending",
        "approved_by": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    result = leave_col().insert_one(leave)
    leave["_id"] = result.inserted_id

    return serialize_mongo_doc(leave)


# =========================
# GET MY LEAVES (with pagination)
# =========================
def get_my_leaves_service(
    user_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    status: str = None,      
    date_filter: str = None  
):
    skip = (page - 1) * limit
    direction = -1 if sort_order == "desc" else 1

    allowed = ["created_at", "start_date", "status"]
    if sort_by not in allowed:
        sort_by = "created_at"
    
    query = {"user_id": ObjectId(user_id)}
   
    if status:
        query["status"] = status.lower()
   
    if date_filter:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        if date_filter == "today":
            query["created_at"] = {"$gte": today_start}
        elif date_filter == "yesterday":
            query["created_at"] = {"$gte": yesterday_start, "$lt": today_start}
        elif date_filter == "older":
            query["created_at"] = {"$lt": yesterday_start}

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
        "data": serialize_mongo_doc(leaves)
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
    sort_order: str = "desc",
    search_term: str = None,
    status: str = None,       
    date_filter: str = None,
    exact_date: str = None,
    month_year: str = None
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

    base_match = {"workspace_id": ObjectId(workspace_id)}
    
    if status:
        base_match["status"] = status.lower()

    if exact_date:
        target_date = datetime.strptime(exact_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        next_day = target_date + timedelta(days=1)
        base_match["created_at"] = {"$gte": target_date, "$lt": next_day}
    
    elif month_year:
        target_month = datetime.strptime(month_year, "%Y-%m").replace(tzinfo=timezone.utc)
        # Advance to the 1st of the next month
        next_month = (target_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        base_match["created_at"] = {"$gte": target_month, "$lt": next_month}
        
    elif date_filter:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        if date_filter == "today":
            base_match["created_at"] = {"$gte": today_start}
        elif date_filter == "yesterday":
            base_match["created_at"] = {"$gte": yesterday_start, "$lt": today_start}
        elif date_filter == "older":
            base_match["created_at"] = {"$lt": yesterday_start}

    pipeline = [
        {"$match": base_match},
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}}
    ]

    if search_term:
        pipeline.append({
            "$match": {
                "$or": [
                    {"user.name": {"$regex": search_term, "$options": "i"}},
                    {"user.email": {"$regex": search_term, "$options": "i"}},
                    {"leave_type": {"$regex": search_term, "$options": "i"}},
                    {"reason": {"$regex": search_term, "$options": "i"}}
                ]
            }
        })

    count_pipeline = pipeline.copy()
    count_pipeline.append({"$count": "total"})
    count_res = list(leave_col().aggregate(count_pipeline))
    total = count_res[0]["total"] if count_res else 0

    pipeline.extend([
        {"$sort": {sort_by: direction}},
        {"$skip": skip},
        {"$limit": limit}
    ])

    data = list(leave_col().aggregate(pipeline))

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": serialize_mongo_doc(data)
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

    current_start_date = leave.get("start_date")
    current_end_date = leave.get("end_date")

    next_start_date = start_date if start_date is not None else current_start_date
    next_end_date = end_date if end_date is not None else current_end_date

    normalized_start_date, normalized_end_date, error = _validate_leave_dates(
        next_start_date,
        next_end_date
    )

    if error:
        return error

    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if leave_type is not None:
        update_data["leave_type"] = leave_type

    if reason is not None:
        update_data["reason"] = reason

    if start_date is not None:
        update_data["start_date"] = normalized_start_date

    if end_date is not None:
        update_data["end_date"] = normalized_end_date

    leave_col().update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": update_data}
    )

    updated_leave = leave_col().find_one({"_id": ObjectId(leave_id)})
    return serialize_mongo_doc(updated_leave)


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

    leave_col().update_one(
        {"_id": ObjectId(leave_id)},
        {
            "$set": {
                "status": status,
                "approved_by": ObjectId(owner_id),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    start_dt = _parse_leave_date(leave.get("start_date"))
    end_dt = _parse_leave_date(leave.get("end_date"))

    if not start_dt or not end_dt:
        return "invalid_leave_dates"

    delta = end_dt - start_dt
    
    date_list = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

    if status == "approved":
        for date_str in date_list:
            attendance_col().update_one(
                {
                    "workspace_id": leave["workspace_id"],
                    "user_id": leave["user_id"],
                    "date": date_str
                },
                {
                    "$set": {
                        "status": "present", 
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "check_in": None,
                        "check_out": None,
                        "face_verified": False,
                        "liveness_verified": False,
                        "mock_location_detected": False,
                        "latitude": 0.0,
                        "longitude": 0.0,
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
    elif status == "rejected":
        attendance_col().delete_many({
            "workspace_id": leave["workspace_id"],
            "user_id": leave["user_id"],
            "date": {"$in": date_list}
        })

    updated_leave = leave_col().find_one({"_id": ObjectId(leave_id)})
    return serialize_mongo_doc(updated_leave)


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

    return serialize_mongo_doc(leave)