from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def geofence_col():
    return collections("geofences")


def get_geofence_service(workspace_id: str):
    return geofence_col().find_one({
        "workspace_id": ObjectId(workspace_id)
    })


def list_workspaces_geofences_service(workspace_id: str):
    return list(geofence_col().find({"workspace_id": ObjectId(workspace_id)}))


# =========================
# CREATE NEW GEOFENCE
# =========================
def create_new_geofence_service(
    workspace_id: str,
    user_id: str,
    name: str,
    latitude: float,
    longitude: float,
    radius_meters: int,
    status: str = "inactive"
):
    workspace_obj_id = ObjectId(workspace_id)
    user_obj_id = ObjectId(user_id)

    
    if status == "active":
        member_col = collections("workspace_members")
        owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
        workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]

        if workspace_ids:
            geofence_col().update_many(
                {"workspace_id": {"$in": workspace_ids}, "status": "active"},
                {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
            )

    new_geofence = {
        "workspace_id": workspace_obj_id,
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "radius_meters": radius_meters,
        "status": status,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    res = geofence_col().insert_one(new_geofence)
    new_geofence["_id"] = res.inserted_id
    return new_geofence


# =========================
# UPDATE BY ID
# =========================
def update_geofence_service(
    workspace_id: str,
    geofence_id: str,
    user_id: str,
    name: str | None,
    latitude: float | None,
    longitude: float | None,
    radius_meters: int | None,
    status: str | None = None
):
    workspace_obj_id = ObjectId(workspace_id)
    geofence_obj_id = ObjectId(geofence_id)
    user_obj_id = ObjectId(user_id)

    if status == "active":
        member_col = collections("workspace_members")
        owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
        workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]

        if workspace_ids:
            geofence_col().update_many(
                {"workspace_id": {"$in": workspace_ids}, "status": "active"},
                {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
            )

    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if name is not None:
        update_data["name"] = name
    if latitude is not None:
        update_data["latitude"] = latitude
    if longitude is not None:
        update_data["longitude"] = longitude
    if radius_meters is not None:
        update_data["radius_meters"] = radius_meters
    if status is not None:
        update_data["status"] = status

    result = geofence_col().update_one(
        {"_id": geofence_obj_id, "workspace_id": workspace_obj_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return geofence_col().find_one({"_id": geofence_obj_id, "workspace_id": workspace_obj_id})


# =========================
# DELETE GEOFENCE
# =========================
def delete_geofence_service(workspace_id: str, geofence_id: str):
    workspace_obj_id = ObjectId(workspace_id)
    geofence_obj_id = ObjectId(geofence_id)

    total_geofences = geofence_col().count_documents({"workspace_id": workspace_obj_id})
    if total_geofences <= 1:
        return {"success": False, "error": "Cannot delete the last remaining geofence."}

   
    target_geofence = geofence_col().find_one({
        "_id": geofence_obj_id,
        "workspace_id": workspace_obj_id
    })
    if not target_geofence:
        return {"success": False, "error": "Geofence not found."}


    if target_geofence.get("status") == "active":
        return {"success": False, "error": "Cannot delete an active geofence."}

    # 4. Perform deletion safely
    geofence_col().delete_one({"_id": geofence_obj_id})
    return {"success": True}

# =========================
# ACTIVATE / SWITCH GEOFENCE
# =========================
def activate_geofence_service(workspace_id: str, geofence_id: str, user_id: str):
    workspace_obj_id = ObjectId(workspace_id)
    geofence_obj_id = ObjectId(geofence_id)
    user_obj_id = ObjectId(user_id)

   
    target = geofence_col().find_one({"_id": geofence_obj_id, "workspace_id": workspace_obj_id})
    if not target:
        return None


    member_col = collections("workspace_members")
    owner_workspaces = member_col.find({"user_id": user_obj_id, "role": "owner"}, {"workspace_id": 1})
    workspace_ids = [entry["workspace_id"] for entry in owner_workspaces]

    if workspace_ids:
    
        geofence_col().update_many(
            {"workspace_id": {"$in": workspace_ids}, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(timezone.utc)}}
        )

    geofence_col().update_one(
        {"_id": geofence_obj_id, "workspace_id": workspace_obj_id},
        {"$set": {"status": "active", "updated_at": datetime.now(timezone.utc)}}
    )

    return geofence_col().find_one({"_id": geofence_obj_id, "workspace_id": workspace_obj_id})