from datetime import datetime, timezone
from bson import ObjectId
from src.config.mongo import collections


def policy_col():
    return collections("attendance_policies")


def get_policy_service(workspace_id: str):
    return policy_col().find_one({
        "workspace_id": ObjectId(workspace_id)
    })

# =========================
# UPDATE POLICY
# =========================
def update_policy_service(
    workspace_id: str,
    check_in_start: str | None,
    check_in_end: str | None,
    late_buffer_minutes: int | None,
    deadline_scan_minutes: int | None,
    annual_leave_limit: int | None,
    sick_leave_limit: int | None
):
    update_data = {
        "updated_at": datetime.now(timezone.utc)
    }

    if check_in_start is not None:
        update_data["check_in_start"] = check_in_start

    if check_in_end is not None:
        update_data["check_in_end"] = check_in_end

    if late_buffer_minutes is not None:
        update_data["late_buffer_minutes"] = late_buffer_minutes

    if deadline_scan_minutes is not None:
        update_data["deadline_scan_minutes"] = deadline_scan_minutes

    if annual_leave_limit is not None:
        update_data["annual_leave_limit"] = annual_leave_limit

    if sick_leave_limit is not None:
        update_data["sick_leave_limit"] = sick_leave_limit

    result = policy_col().update_one(
        {"workspace_id": ObjectId(workspace_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None

    return policy_col().find_one({"workspace_id": ObjectId(workspace_id)})