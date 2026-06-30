from bson import ObjectId
from datetime import datetime, timezone

from src.config.mongo import collections


def holiday_col():
    return collections("holidays")


# =========================
# CREATE HOLIDAY
# =========================
def create_holiday_service(
    workspace_id: str,
    name: str,
    date: str
):
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


# =========================
# GET ALL HOLIDAYS
# =========================
def get_holidays_service(
    workspace_id: str,
    page: int = 1,
    limit: int = 10
):
    skip = (page - 1) * limit

    holidays = list(
        holiday_col()
        .find({
            "workspace_id": ObjectId(workspace_id)
        })
        .sort("date", 1)
        .skip(skip)
        .limit(limit)
    )

    total = holiday_col().count_documents({
        "workspace_id": ObjectId(workspace_id)
    })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "data": holidays
    }


# =========================
# GET ONE HOLIDAY
# =========================
def get_holiday_service(
    holiday_id: str
):
    return holiday_col().find_one({
        "_id": ObjectId(holiday_id)
    })


# =========================
# UPDATE HOLIDAY
# =========================
def update_holiday_service(
    holiday_id: str,
    name: str | None,
    date: str | None
):
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if name is not None:
        update_data["name"] = name

    if date is not None:
        update_data["date"] = date

    result = holiday_col().update_one(
        {"_id": ObjectId(holiday_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return holiday_col().find_one({
        "_id": ObjectId(holiday_id)
    })


# =========================
# DELETE HOLIDAY
# =========================
def delete_holiday_service(
    holiday_id: str
):
    result = holiday_col().delete_one({
        "_id": ObjectId(holiday_id)
    })

    return result.deleted_count > 0