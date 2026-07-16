from datetime import datetime, timezone, timedelta
from bson import ObjectId
from src.config.mongo import collections

# Define the UTC+7 Local Timezone
LOCAL_TZ = timezone(timedelta(hours=7))

def policy_col():
    return collections("attendance_policies")

def get_policy_service(workspace_id: str):
    policy = policy_col().find_one({"workspace_id": ObjectId(workspace_id), "status": "active"})
    if not policy:
        policy = policy_col().find_one({"workspace_id": ObjectId(workspace_id)})
    return policy

def list_workspace_policies_service(workspace_id: str, search_term: str = None):
    query = {"workspace_id": ObjectId(workspace_id)}
    
    if search_term:
        query["name"] = {"$regex": search_term, "$options": "i"}
        
    return list(policy_col().find(query))

def create_new_policy_service(workspace_id: str, user_id: str, data: dict):
    workspace_obj_id = ObjectId(workspace_id)

    # Set existing active policies strictly in THIS workspace to inactive
    policy_col().update_many(
        {"workspace_id": workspace_obj_id, "status": "active"},
        {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
    )

    new_policy = {
        "workspace_id": workspace_obj_id,
        "name": data["name"],
        "work_start_time": data["work_start_time"],
        "work_end_time": data["work_end_time"],
        "check_in_start": data["check_in_start"],
        "check_out_start": data["check_out_start"],
        "late_buffer_minutes": data["late_buffer_minutes"],
        "deadline_scan_minutes": data["deadline_scan_minutes"],
        "annual_leave_limit": data["annual_leave_limit"],
        "sick_leave_limit": data["sick_leave_limit"],
        "status": "active",  
        "created_at": datetime.now(LOCAL_TZ),
        "updated_at": datetime.now(LOCAL_TZ)
    }

    res = policy_col().insert_one(new_policy)
    new_policy["_id"] = res.inserted_id
    return new_policy

def update_policy_service(workspace_id: str, policy_id: str, user_id: str, data: dict):
    workspace_obj_id = ObjectId(workspace_id)
    policy_obj_id = ObjectId(policy_id)

    if data.get("status") == "active":
        # Deactivate other active policies in this workspace only
        policy_col().update_many(
            {"workspace_id": workspace_obj_id, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
        )

    update_data = {"updated_at": datetime.now(LOCAL_TZ)}
    for key, val in data.items():
        if val is not None:
            update_data[key] = val

    result = policy_col().update_one(
        {"_id": policy_obj_id, "workspace_id": workspace_obj_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})

def delete_policy_service(workspace_id: str, policy_id: str):
    workspace_obj_id = ObjectId(workspace_id)
    policy_obj_id = ObjectId(policy_id)

    if policy_col().count_documents({"workspace_id": workspace_obj_id}) <= 1:
        return {"success": False, "error": "Cannot delete your last remaining attendance policy configuration."}

    target = policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})
    if not target:
        return {"success": False, "error": "Attendance policy not found."}

    if target.get("status") == "active":
        return {"success": False, "error": "Cannot delete an active policy. Switch to another policy first."}

    policy_col().delete_one({"_id": policy_obj_id})
    return {"success": True}

def activate_policy_service(workspace_id: str, policy_id: str, user_id: str):
    workspace_obj_id = ObjectId(workspace_id)
    policy_obj_id = ObjectId(policy_id)

    target = policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})
    if not target:
        return None

    # Deactivate other active policies in this workspace only
    policy_col().update_many(
        {"workspace_id": workspace_obj_id, "status": "active"},
        {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
    )

    policy_col().update_one(
        {"_id": policy_obj_id, "workspace_id": workspace_obj_id},
        {"$set": {"status": "active", "updated_at": datetime.now(LOCAL_TZ)}}
    )

    return policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})