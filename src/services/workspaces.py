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

def attendance_col():
    return collections("attendances")

##========================
## WORKSPACE SERVICES
#========================
def get_workspaces_for_user_service(user_id: str):
    workspace_ids = member_col().find({"user_id": ObjectId(user_id)}, {"workspace_id": 1})
    workspace_ids = [entry["workspace_id"] for entry in workspace_ids]

    workspaces = workspace_col().find({"_id": {"$in": workspace_ids}})
    return list(workspaces)

# =========================
# CREATE WORKSPACE
# =========================
def create_workspace_service(workspace_name: str, description: str):
    workspace = {
        "workspace_name": workspace_name,
        "description": description,
        "status": "active",
        "created_at": datetime.now(timezone.utc)
    }

    res = workspace_col().insert_one(workspace)
    workspace["_id"] = res.inserted_id

    workspace_id = workspace["_id"]

    # =========================
    # AUTO CREATE GEOFENCE
    # =========================
    geofence_col().insert_one({
        "workspace_id": workspace_id,
        "name": "Main Office",
        "latitude": 0.0,
        "longitude": 0.0,
        "radius_meters": 100,
        "created_at": datetime.now(timezone.utc)
    })

    # =========================
    # AUTO CREATE POLICY
    # =========================
    policy_col().insert_one({
        "workspace_id": workspace_id,
        "check_in_start": "08:00",
        "check_in_end": "09:00",
        "late_buffer_minutes": 10,
        "deadline_scan_minutes": 15,
        "annual_leave_limit": 18,
        "sick_leave_limit": 12,
        "created_at": datetime.now(timezone.utc)
    })

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

    # delete geofence
    geofence_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete attendance policy
    policy_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete leaves
    leave_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete holidays
    holiday_col().delete_many({
        "workspace_id": workspace_object_id
    })

    # delete attendances
    attendance_col().delete_many({
        "workspace_id": workspace_object_id
    })

    return workspace