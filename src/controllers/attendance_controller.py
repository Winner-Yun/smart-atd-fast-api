import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
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


router = APIRouter(
    tags=["Attendance"]
)

bearer = HTTPBearer(auto_error=False)



def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials
):

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


    user = get_current_user_from_token(
        credentials.credentials
    )


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


    return user

CRON_SECRET = os.getenv("CRON_SECRET", "my_secret_token_123")

def verify_cron(x_cron_token: str = Header(None)):
    if x_cron_token != CRON_SECRET:
        raise HTTPException(status_code=404, detail="Not Found")

@router.post(
    "/internal/attendance/auto-mark-absences",
    dependencies=[Depends(verify_cron)],
    include_in_schema=False 
)
def run_auto_mark_absences():
    from src.services.attendance_service import auto_mark_absences_service
    
    count = auto_mark_absences_service()
    return {"status": "success", "marked_records": count}

# =========================
# CHECK IN
# =========================

@router.post(
    "/{workspace_id}/attendance/check-in",
    response_model=AttendanceResponse
)
def check_in(
    workspace_id: str,
    payload: CheckInRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


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
            status_code=403,
            detail="You are not a member of this workspace"
        )


    if attendance == "already_checked_in":
        raise HTTPException(
            status_code=400,
            detail="Already checked in today"
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



# =========================
# CHECK OUT
# =========================

@router.post(
    "/{workspace_id}/attendance/check-out"
)
def check_out(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    attendance = create_checkout_service(
        workspace_id,
        str(user["_id"])
    )


    if attendance == "not_member":
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this workspace"
        )


    if not attendance:
        raise HTTPException(
            status_code=404,
            detail="No attendance found for today"
        )


    return {
        "message": "Checked out successfully"
    }



# =========================
# GET MY ATTENDANCE
# =========================

@router.get(
    "/{workspace_id}/me",
    summary="Get My Attendance Logs",
    description="Fetches the authenticated user's attendance records for a specific workspace. Includes optional filtering for UI dropdowns."
)
def get_my_attendance(
    workspace_id: str,
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of records per page"),
    sort_by: str = Query("date", description="Field to sort by (date, created_at, check_in, status)"),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)"),
    status: Optional[str] = Query(None, description="Filter by attendance status. Valid options: 'present', 'late', 'absent'"),
    date_filter: Optional[str] = Query(None, description="Filter by relative date. Valid options: 'today', 'yesterday', 'older'"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    **How to use filters from the frontend:**
    - To get everything: `GET /workspaces/{workspace_id}/attendance/me`
    - To get only late records: `GET /workspaces/{workspace_id}/attendance/me?status=late`
    - To get yesterday's records: `GET /workspaces/{workspace_id}/attendance/me?date_filter=yesterday`
    - To combine filters (e.g., absent yesterday): `GET /workspaces/{workspace_id}/attendance/me?status=absent&date_filter=yesterday`
    """
    user = get_authenticated_user(credentials)

    result = get_my_attendance_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order,
        status=status,
        date_filter=date_filter
    )

    if result == "not_member":
        raise HTTPException(
            status_code=403,
            detail="Not a member"
        )

    return result