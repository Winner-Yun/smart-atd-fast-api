from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.services.auth_service import get_current_user_from_token

from src.services.attendance_service import (
    create_checkin_service,
    create_checkout_service,
    get_my_attendance_service
)

from src.models.attendance_model import (
    CheckInRequest,
    AttendanceResponse
)

attendance_router = APIRouter(
    tags=["Attendance"]
)

bearer = HTTPBearer(auto_error=False)


@attendance_router.post(
    "/{workspace_id}/attendance/check-in",
    response_model=AttendanceResponse
)
def check_in(
    workspace_id: str,
    payload: CheckInRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    attendance = create_checkin_service(
        workspace_id,
        str(user["_id"]),
        payload.latitude,
        payload.longitude,
        payload.face_verified,
        payload.liveness_verified,
        payload.mock_location_detected
    )

    if attendance == "not_member":
        raise HTTPException(
            403,
            "You are not a member of this workspace"
        )

    if attendance == "already_checked_in":
        raise HTTPException(
            400,
            "Already checked in today"
        )

    return AttendanceResponse(
        id=str(attendance["_id"]),
        workspace_id=str(attendance["workspace_id"]),
        user_id=str(attendance["user_id"]),
        date=attendance["date"],
        check_in=attendance["check_in"],
        check_out=attendance["check_out"],
        status=attendance["status"],
        face_verified=attendance["face_verified"],
        liveness_verified=attendance["liveness_verified"],
        mock_location_detected=attendance["mock_location_detected"],
        latitude=attendance["latitude"],
        longitude=attendance["longitude"],
        created_at=attendance["created_at"],
        updated_at=attendance.get("updated_at")
    )


@attendance_router.post(
    "/{workspace_id}/attendance/check-out"
)
def check_out(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    attendance = create_checkout_service(
        workspace_id,
        str(user["_id"])
    )

    if attendance == "not_member":
        raise HTTPException(
            403,
            "You are not a member of this workspace"
        )

    if not attendance:
        raise HTTPException(
            404,
            "No attendance found for today"
        )

    return {
        "message": "Checked out successfully"
    }


@attendance_router.get("/{workspace_id}/me")
def get_my_attendance(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "date",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = get_my_attendance_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )

    if result == "not_member":
        raise HTTPException(403, "Not a member")

    return result