from datetime import datetime, timezone, timedelta
from bson import ObjectId
from src.config.mongo import collections

# Define the UTC+7 Local Timezone
LOCAL_TZ = timezone(timedelta(hours=7))

def geofence_col():
    return collections("geofences")

def get_geofence_service(workspace_id: str):
    return geofence_col().find_one({
        "workspace_id": ObjectId(workspace_id)
    })

def list_workspaces_geofences_service(workspace_id: str, search_term: str = None):
    query = {"workspace_id": ObjectId(workspace_id)}
    
    if search_term:
        query["name"] = {"$regex": search_term, "$options": "i"}
        
    return list(geofence_col().find(query))

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

    if status == "active":
        geofence_col().update_many(
            {"workspace_id": workspace_obj_id, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
        )

    new_geofence = {
        "workspace_id": workspace_obj_id,
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "radius_meters": radius_meters,
        "status": status,
        "created_at": datetime.now(LOCAL_TZ),
        "updated_at": datetime.now(LOCAL_TZ)
    }

    res = geofence_col().insert_one(new_geofence)
    new_geofence["_id"] = res.inserted_id
    return new_geofence

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

    if status == "active":
        geofence_col().update_many(
            {"workspace_id": workspace_obj_id, "status": "active"},
            {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
        )

    update_data = {
        "updated_at": datetime.now(LOCAL_TZ)
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

    geofence_col().delete_one({"_id": geofence_obj_id})
    return {"success": True}

def activate_geofence_service(workspace_id: str, geofence_id: str, user_id: str):
    workspace_obj_id = ObjectId(workspace_id)
    geofence_obj_id = ObjectId(geofence_id)

    target = geofence_col().find_one({"_id": geofence_obj_id, "workspace_id": workspace_obj_id})
    if not target:
        return None

    geofence_col().update_many(
        {"workspace_id": workspace_obj_id, "status": "active"},
        {"$set": {"status": "inactive", "updated_at": datetime.now(LOCAL_TZ)}}
    )

    geofence_col().update_one(
        {"_id": geofence_obj_id, "workspace_id": workspace_obj_id},
        {"$set": {"status": "active", "updated_at": datetime.now(LOCAL_TZ)}}
    )

    return geofence_col().find_one({"_id": geofence_obj_id, "workspace_id": workspace_obj_id})