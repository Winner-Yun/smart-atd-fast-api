from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def workspace_col():
    return collections("workspaces")


def member_col():
    return collections("workspace_members")


def geofence_col():
    return collections("geofences")


def policy_col():
    return collections("attendance_policies")


def invite_col():
    return collections("workspace_invites")


def leave_col():
    return collections("leave_requests")


def holiday_col():
    return collections("holidays")


def holiday_config_col():
    return collections("holiday_configs")


def attendance_col():
    return collections("attendances")


##========================
## WORKSPACE src.services
#========================
def get_workspaces_for_user_service(
    user_id: str, 
    search: str | None = None, 
    sort: str = "asc", 
    only_owner: bool = True
):
    query = {}

    if only_owner:
        owner_workspaces = member_col().find(
            {
                "user_id": ObjectId(user_id),
                "role": "owner"
            },
            {
                "workspace_id": 1
            }
        )
        workspace_ids = [
            entry["workspace_id"]
            for entry in owner_workspaces
        ]

        query["_id"] = {
            "$in": workspace_ids
        }

    if search:
        query["workspace_name"] = {"$regex": search, "$options": "i"}

    direction = 1 if sort.lower() == "asc" else -1

    workspaces = workspace_col().find(query).sort("workspace_name", direction)
    return list(workspaces)


# =========================
# CREATE WORKSPACE
# =========================
def create_workspace_service(user_id: str, workspace_name: str, description: str):
    """
    Creates a new active workspace and geofence, while deactivating 
    any older workspaces/geofences owned by the same user.
    """
    user_obj_id = ObjectId(user_id)

    owner_workspaces = member_col().find(
        {
            "user_id": user_obj_id,
            "role": "owner"
        },
        {
            "workspace_id": 1
        }
    )
    old_workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]

    if old_workspace_ids:
        # Deactivate old workspaces
        workspace_col().update_many(
            {"_id": {"$in": old_workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
        )
        # Deactivate old geofences
        geofence_col().update_many(
            {"workspace_id": {"$in": old_workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
        )
        # Deactivate old policies
        policy_col().update_many(
            {"workspace_id": {"$in": old_workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
        )

    workspace = {
        "workspace_name": workspace_name,
        "description": description,
        "status": "active",
        "created_at": datetime.now(timezone.utc)
    }

    res = workspace_col().insert_one(workspace)
    workspace_id = res.inserted_id
    workspace["_id"] = workspace_id

    geofence_col().insert_one({
        "workspace_id": workspace_id,
        "name": "Main Office",
        "latitude": 0.0,
        "longitude": 0.0,
        "radius_meters": 100,
        "status": "active",
        "created_at": datetime.now(timezone.utc)
    })

    policy_col().insert_one({
        "workspace_id": workspace_id,
        "name": "Default Policy",
        "work_start_time": "08:00 AM",
        "work_end_time": "05:00 PM",
        "check_in_start": "07:30 AM",
        "check_out_start": "04:30 PM",
        "late_buffer_minutes": 15,
        "deadline_scan_minutes": 30,
        "annual_leave_limit": 18,
        "sick_leave_limit": 6,
        "status": "active", 
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })

    # Auto create default holiday config
    holiday_config_col().insert_one({
        "workspace_id": workspace_id,
        "include_public_holidays": True,
        "include_weekend": "Saturday and Sunday",
        "updated_at": datetime.now(timezone.utc)
    })
    
    add_owner_service(str(workspace_id), user_id)

    return workspace


# =========================
# ADD OWNER
# =========================
def add_owner_service(
    workspace_id: str,
    user_id: str
):
    member = {
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "role": "owner",
        "joined_at": datetime.now(timezone.utc)
    }

    member_col().insert_one(member)


# =========================
# CHECK OWNER
# =========================
def check_owner(
    workspace_id: str,
    user_id: str
):
    return member_col().find_one({
        "workspace_id": ObjectId(workspace_id),
        "user_id": ObjectId(user_id),
        "role": "owner"
    })


# =========================
# UPDATE WORKSPACE
# =========================
def update_workspace_service(
    workspace_id: str,
    workspace_name: str | None,
    description: str | None,
    status: str | None
):
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if workspace_name is not None:
        update_data["workspace_name"] = workspace_name

    if description is not None:
        update_data["description"] = description

    if status is not None:
        update_data["status"] = status

    result = workspace_col().update_one(
        {"_id": ObjectId(workspace_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return workspace_col().find_one({
        "_id": ObjectId(workspace_id)
    })


# =========================
# DELETE WORKSPACE
# =========================
def delete_workspace_service(workspace_id: str):

    workspace = workspace_col().find_one({
        "_id": ObjectId(workspace_id)
    })

    if not workspace:
        return None

    workspace_object_id = ObjectId(workspace_id)

    # delete workspace
    workspace_col().delete_one({
        "_id": workspace_object_id
    })

    # delete members
    member_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete invites
    invite_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete geofences
    geofence_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete attendance policies
    policy_col().delete_many({
        "workspace_id": workspace_object_id
    })

    leave_col().delete_many({
        "workspace_id": workspace_object_id
    })

    holiday_col().delete_many({
        "workspace_id": workspace_object_id
    })
    
    holiday_config_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete attendances
    attendance_col().delete_many({
        "workspace_id": workspace_object_id
    })

    return workspace