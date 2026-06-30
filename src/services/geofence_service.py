from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def geofence_col():
    return collections("geofences")


def get_geofence_service(workspace_id: str):
    return geofence_col().find_one({
        "workspace_id": ObjectId(workspace_id)
    })

# =========================
# UPDATE
# =========================
def update_geofence_service(
    workspace_id: str,
    name: str | None,
    latitude: float | None,
    longitude: float | None,
    radius_meters: int | None
):
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

    result = geofence_col().update_one(
        {"workspace_id": ObjectId(workspace_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return geofence_col().find_one({"workspace_id": ObjectId(workspace_id)})