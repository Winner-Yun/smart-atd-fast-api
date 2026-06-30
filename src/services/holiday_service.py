from bson import ObjectId
from datetime import datetime, timezone
from src.config.mongo import collections

def holiday_col():
    return collections("holidays")

def holiday_config_col():
    return collections("holiday_configs")

# =========================
# HOLIDAY CONFIGURATION
# =========================
def get_holiday_config_service(workspace_id: str):
    config = holiday_config_col().find_one({"workspace_id": ObjectId(workspace_id)})
    
    # Return default settings if the owner hasn't configured them yet
    if not config:
        return {
            "workspace_id": ObjectId(workspace_id),
            "include_public_holidays": True,
            "include_weekend": "Saturday and Sunday",
            "updated_at": datetime.now(timezone.utc)
        }
    return config

def update_holiday_config_service(
    workspace_id: str, 
    include_public_holidays: bool | None, 
    include_weekend: str | None
):
    workspace_obj_id = ObjectId(workspace_id)
    config = holiday_config_col().find_one({"workspace_id": workspace_obj_id})
    
    update_data = {"updated_at": datetime.now(timezone.utc)}
    
    if include_public_holidays is not None:
        update_data["include_public_holidays"] = include_public_holidays
    if include_weekend is not None:
        update_data["include_weekend"] = include_weekend

    if not config:
        # Upsert: Create baseline if it doesn't exist
        if include_public_holidays is None: update_data["include_public_holidays"] = True
        if include_weekend is None: update_data["include_weekend"] = "Saturday and Sunday"
        update_data["workspace_id"] = workspace_obj_id
        
        holiday_config_col().insert_one(update_data)
        return update_data
    else:
        # Update existing
        holiday_config_col().update_one(
            {"workspace_id": workspace_obj_id}, 
            {"$set": update_data}
        )
        config.update(update_data)
        return config


# =========================
# CUSTOM HOLIDAYS (Your Existing Logic)
# =========================
def create_holiday_service(workspace_id: str, name: str, date: str):
    holiday = {
        "workspace_id": ObjectId(workspace_id),
        "name": name,
        "date": date,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    result = holiday_col().insert_one(holiday)
    holiday["_id"] = result.inserted_id
    return holiday

def get_holidays_service(workspace_id: str, page: int = 1, limit: int = 10):
    skip = (page - 1) * limit
    holidays = list(holiday_col().find({"workspace_id": ObjectId(workspace_id)}).sort("date", 1).skip(skip).limit(limit))
    total = holiday_col().count_documents({"workspace_id": ObjectId(workspace_id)})
    return {"page": page, "limit": limit, "total": total, "data": holidays}

def get_holiday_service(holiday_id: str):
    return holiday_col().find_one({"_id": ObjectId(holiday_id)})

def update_holiday_service(holiday_id: str, name: str | None, date: str | None):
    update_data = {"updated_at": datetime.now(timezone.utc)}
    if name is not None: update_data["name"] = name
    if date is not None: update_data["date"] = date
    result = holiday_col().update_one({"_id": ObjectId(holiday_id)}, {"$set": update_data})
    if result.matched_count == 0: return None
    return holiday_col().find_one({"_id": ObjectId(holiday_id)})

def delete_holiday_service(holiday_id: str):
    result = holiday_col().delete_one({"_id": ObjectId(holiday_id)})
    return result.deleted_count > 0