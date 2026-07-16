from bson import ObjectId
from datetime import datetime, timedelta, timezone
from datetime import time as dt_time

from src.services.holiday_service import is_working_day
from src.services.attendance_policy_service import get_policy_service
from src.config.mongo import collections

# Define the UTC+7 Local Timezone
LOCAL_TZ = timezone(timedelta(hours=7))


def attendance_col():
    return collections("attendances")


def member_col():
    return collections("workspace_members")


def policy_col():
    return collections("attendance_policies")


def geofence_col():
    return collections("geofences")


def _parse_policy_time(time_value: str) -> dt_time:
    time_str = time_value.strip()
    
    try:
        # Try parsing as 24-hour format (e.g., "19:30")
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        pass
        
    try:
        # Fallback to 12-hour format (e.g., "07:30 PM")
        return datetime.strptime(time_str, "%I:%M %p").time()
    except ValueError:
        pass
        
    try:
        # Fallback for 24-hour format with seconds (e.g., "19:30:00")
        return datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        raise ValueError(f"Time data '{time_str}' does not match recognized formats (%H:%M, %I:%M %p, or %H:%M:%S)")


def _get_absence_deadline(workspace_id: str, reference_dt: datetime) -> datetime | None:
    policy = get_policy_service(workspace_id)
    if not policy:
        return None

    check_out_start = policy.get("check_out_start")
    deadline_scan_minutes = policy.get("deadline_scan_minutes")

    if not check_out_start or deadline_scan_minutes is None:
        return None

    # Strictly use UTC+7 local context directly
    check_out_time = _parse_policy_time(check_out_start)
    local_deadline = reference_dt.replace(
        hour=check_out_time.hour,
        minute=check_out_time.minute,
        second=0,
        microsecond=0,
    )

    final_deadline = local_deadline + timedelta(minutes=int(deadline_scan_minutes))
    return final_deadline.astimezone(LOCAL_TZ)


def create_checkin_service(
    workspace_id: str,
    user_id: str,
    latitude: float,
    longitude: float,
    face_verified: bool,
    liveness_verified: bool,
    mock_location_detected: bool
):
    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if not member:
        return "not_member"

    # Strictly UTC+7 local date
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")

    existing = attendance_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "date": today
    })

    if existing:
        # If an automatic 'absent' placeholder exists, overwrite it with an actual check-in
        if existing.get("status") == "absent" and existing.get("check_in") is None:
            attendance_col().update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "check_in": datetime.now(LOCAL_TZ),
                        "status": "present",  # Switches from absent to present
                        "face_verified": face_verified,
                        "liveness_verified": liveness_verified,
                        "mock_location_detected": mock_location_detected,
                        "latitude": latitude,
                        "longitude": longitude,
                        "updated_at": datetime.now(LOCAL_TZ)
                    }
                }
            )
            return attendance_col().find_one({"_id": existing["_id"]})
            
        return "already_checked_in"

    attendance = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "date": today,
        "check_in": datetime.now(LOCAL_TZ),
        "check_out": None,
        "status": "present",
        "face_verified": face_verified,
        "liveness_verified": liveness_verified,
        "mock_location_detected": mock_location_detected,
        "latitude": latitude,
        "longitude": longitude,
        "created_at": datetime.now(LOCAL_TZ),
        "updated_at": None
    }

    result = attendance_col().insert_one(attendance)
    attendance["_id"] = result.inserted_id
    return attendance


def create_checkout_service(workspace_id: str, user_id: str):
    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if not member:
        return "not_member"

    # Strictly UTC+7 local date
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")

    attendance = attendance_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "date": today
    })

    if not attendance:
        return None

    attendance_col().update_one(
        {"_id": attendance["_id"]},
        {
            "$set": {
                "check_out": datetime.now(LOCAL_TZ),
                "updated_at": datetime.now(LOCAL_TZ)
            }
        }
    )

    return attendance_col().find_one({"_id": attendance["_id"]})


def get_my_attendance_service(
    workspace_id: str,
    user_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "date",
    sort_order: str = "desc",
    status: str = None,      
    date_filter: str = None  
):
    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if not member:
        return "not_member"

    skip = (page - 1) * limit
    direction = -1 if sort_order == "desc" else 1

    allowed = ["date", "created_at", "check_in", "status"]
    if sort_by not in allowed:
        sort_by = "date"

    query = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    }

    if status:
        query["status"] = status.lower()

    if date_filter:
        now_local = datetime.now(LOCAL_TZ)
        if date_filter == "today":
            query["date"] = now_local.strftime("%Y-%m-%d")
        elif date_filter == "yesterday":
            yesterday = now_local - timedelta(days=1)
            query["date"] = yesterday.strftime("%Y-%m-%d")
        elif date_filter == "older":
            yesterday = now_local - timedelta(days=1)
            query["date"] = {"$lt": yesterday.strftime("%Y-%m-%d")}

    data = list(
        attendance_col()
        .find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(limit)
    )

    total = attendance_col().count_documents(query)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": data
    }


def get_workspace_attendance_service(
    workspace_id: str,
    owner_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "date",
    sort_order: str = "desc",
    search_term: str = None,
    status: str = None,
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

    allowed = ["date", "created_at", "check_in", "check_out"]
    if sort_by not in allowed:
        sort_by = "date"
   
    base_match = {"workspace_id": ObjectId(workspace_id)}
    if status:
        base_match["status"] = status.lower()

    # Apply Exact Date or Month/Year filters
    if exact_date:
        base_match["date"] = exact_date
    elif month_year:
        base_match["date"] = {"$regex": f"^{month_year}"}

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
                    {"user.email": {"$regex": search_term, "$options": "i"}}
                ]
            }
        })

    count_pipeline = pipeline.copy()
    count_pipeline.append({"$count": "total"})
    count_res = list(attendance_col().aggregate(count_pipeline))
    total = count_res[0]["total"] if count_res else 0

    pipeline.extend([
        {"$sort": {sort_by: direction}},
        {"$skip": skip},
        {"$limit": limit}
    ])

    data = list(attendance_col().aggregate(pipeline))

    for item in data:
        item["_id"] = str(item["_id"])
        item["workspace_id"] = str(item["workspace_id"])
        item["user_id"] = str(item["user_id"])
        if "user" in item and item["user"]:
            item["user"]["_id"] = str(item["user"]["_id"])

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": data
    }


# ========================
# AUTO MARK ABSENCES
# ========================

def auto_mark_absences_service():
    today_dt = datetime.now(LOCAL_TZ)
    workspaces = member_col().distinct("workspace_id")
    marked_count = 0
    
    for ws_id in workspaces:
        # CHECK: Workspace must have an active policy and active geofence
        active_policy = policy_col().find_one({
            "workspace_id": ws_id,
            "status": "active"
        })
        
        active_geofence = geofence_col().find_one({
            "workspace_id": ws_id,
            "status": "active"
        })
        
  
        if not active_policy or not active_geofence:
            continue
            
        # Strictly UTC+7 local date mapping
        today_str = today_dt.strftime("%Y-%m-%d")
      
        if not is_working_day(str(ws_id), today_dt):
            continue  

        absence_deadline = _get_absence_deadline(str(ws_id), today_dt)
        if absence_deadline and today_dt < absence_deadline:
            continue
            
        members = member_col().find({"workspace_id": ws_id})
        
        for member in members:
            user_id = member["user_id"]
           
            existing_attendance = attendance_col().find_one({
                "workspace_id": ws_id,
                "user_id": user_id,
                "date": today_str
            })
            
            if existing_attendance:
                has_checked_in = existing_attendance.get("check_in") is not None
                is_on_approved_leave = existing_attendance.get("status") in ["present", "leave"]
                
                if has_checked_in or is_on_approved_leave:
                    continue
            
            if not existing_attendance:
                absent_record = {
                    "workspace_id": ws_id,
                    "user_id": user_id,
                    "date": today_str,
                    "check_in": None,
                    "check_out": None,
                    "status": "absent",
                    "face_verified": False,
                    "liveness_verified": False,
                    "mock_location_detected": False,
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "created_at": today_dt,
                    "updated_at": None
                }
                attendance_col().insert_one(absent_record)
                marked_count += 1
                
            else:
                attendance_col().update_one(
                    {"_id": existing_attendance["_id"]},
                    {
                        "$set": {
                            "status": "absent",
                            "updated_at": today_dt
                        }
                    }
                )
                marked_count += 1
                
    return marked_count