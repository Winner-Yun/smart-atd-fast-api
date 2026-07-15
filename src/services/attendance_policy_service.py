from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections

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
    user_obj_id = ObjectId(user_id)

    # Unconditionally set existing active policies to inactive
    member_col = collections("workspace_members")
    owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
    workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]
    
    # Safeguard: ensure the current workspace is always included in the deactivation update
    if workspace_obj_id not in workspace_ids:
        workspace_ids.append(workspace_obj_id)

    if workspace_ids:
        policy_col().update_many(
            {"workspace_id": {"$in": workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
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
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    res = policy_col().insert_one(new_policy)
    new_policy["_id"] = res.inserted_id
    return new_policy

def update_policy_service(workspace_id: str, policy_id: str, user_id: str, data: dict):
    workspace_obj_id = ObjectId(workspace_id)
    policy_obj_id = ObjectId(policy_id)
    user_obj_id = ObjectId(user_id)

    if data.get("status") == "active":
        member_col = collections("workspace_members")
        owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
        workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]
        if workspace_ids:
            policy_col().update_many(
                {"workspace_id": {"$in": workspace_ids}, "status": "active"},
                {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
            )

    update_data = {"updated_at": datetime.now(timezone.utc)}
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
    user_obj_id = ObjectId(user_id)

    target = policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})
    if not target:
        return None

    member_col = collections("workspace_members")
    owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
    workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]

    if workspace_ids:
      
        policy_col().update_many(
            {"workspace_id": {"$in": workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
        )

    
    policy_col().update_one(
        {"_id": policy_obj_id, "workspace_id": workspace_obj_id},
        {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc)}}
    )

    return policy_col().find_one({"_id": policy_obj_id, "workspace_id": workspace_obj_id})