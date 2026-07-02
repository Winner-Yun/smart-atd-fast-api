from bson import ObjectId
from datetime import datetime, timedelta, timezone

from src.services.holiday_service import is_working_day
from src.config.mongo import collections


def attendance_col():
    return collections("attendances")


def member_col():
    return collections("workspace_members")


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

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    existing = attendance_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "date": today
    })

    if existing:
        return "already_checked_in"

    attendance = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),

        "date": today,

        "check_in": datetime.now(timezone.utc),
        "check_out": None,

        "status": "present",

        "face_verified": face_verified,
        "liveness_verified": liveness_verified,
        "mock_location_detected": mock_location_detected,

        "latitude": latitude,
        "longitude": longitude,

        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }

    result = attendance_col().insert_one(attendance)

    attendance["_id"] = result.inserted_id

    return attendance


def create_checkout_service(
    workspace_id: str,
    user_id: str
):

    member = member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id)
    })

    if not member:
        return "not_member"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    attendance = attendance_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "date": today
    })

    if not attendance:
        return None

    attendance_col().update_one(
        {
            "_id": attendance["_id"]
        },
        {
            "$set": {
                "check_out": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return attendance_col().find_one({
        "_id": attendance["_id"]
    })


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
        now = datetime.now(timezone.utc)
        if date_filter == "today":
            query["date"] = now.strftime("%Y-%m-%d")
        elif date_filter == "yesterday":
            yesterday = now - timedelta(days=1)
            query["date"] = yesterday.strftime("%Y-%m-%d")
        elif date_filter == "older":
            yesterday = now - timedelta(days=1)
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
    status: str = None 
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

    # Search filter matching employee details
    if search_term:
        pipeline.append({
            "$match": {
                "$or": [
                    {"user.name": {"$regex": search_term, "$options": "i"}},
                    {"user.email": {"$regex": search_term, "$options": "i"}}
                ]
            }
        })

    # Get count total
    count_pipeline = pipeline.copy()
    count_pipeline.append({"$count": "total"})
    count_res = list(attendance_col().aggregate(count_pipeline))
    total = count_res[0]["total"] if count_res else 0

    # Sort and paginate
    pipeline.extend([
        {"$sort": {sort_by: direction}},
        {"$skip": skip},
        {"$limit": limit}
    ])

    data = list(attendance_col().aggregate(pipeline))

    # Clean ObjectIds
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

def auto_mark_absences_service():
    today_dt = datetime.now(timezone.utc)
    today_str = today_dt.strftime("%Y-%m-%d")
    
    workspaces = member_col().distinct("workspace_id")
    
    marked_count = 0
    
    for ws_id in workspaces:
      
        if not is_working_day(str(ws_id), today_dt):
            continue  
            
    
        members = member_col().find({"workspace_id": ws_id})
        
        for member in members:
            user_id = member["user_id"]
            
        
            existing_attendance = attendance_col().find_one({
                "workspace_id": ws_id,
                "user_id": user_id,
                "date": today_str
            })
            
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
                
    return marked_count