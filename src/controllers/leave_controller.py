from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.auth import Optional

from src.services.auth_service import get_current_user_from_token
from src.services.leave_service import (
    create_leave_service,
    get_my_leaves_service,
    delete_leave_service,
    update_leave_service
)

from src.models.leave_model import (
    CreateLeaveRequest,
    LeaveResponse
)


router = APIRouter(
    tags=["Leave"]
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



# =========================
# CREATE LEAVE
# =========================

@router.post(
    "/{workspace_id}/leave",
    response_model=LeaveResponse
)
def create_leave(
    workspace_id: str,
    payload: CreateLeaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    leave = create_leave_service(
        workspace_id,
        str(user["_id"]),
        payload.leave_type,
        payload.reason,
        payload.start_date,
        payload.end_date
    )


    if leave == "not_member":
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this workspace"
        )


    if not leave:
        raise HTTPException(
            status_code=400,
            detail="Failed to create leave request"
        )


    return LeaveResponse(
        id=str(leave["_id"]),
        workspace_id=str(leave["workspace_id"]),
        user_id=str(leave["user_id"]),
        leave_type=leave["leave_type"],
        reason=leave["reason"],
        start_date=leave["start_date"],
        end_date=leave["end_date"],
        status=leave["status"],
        approved_by=None,
        created_at=leave["created_at"]
    )



# =========================
# UPDATE LEAVE
# =========================

@router.patch("/{leave_id}")
def update_leave(
    leave_id: str,
    payload: CreateLeaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    leave = update_leave_service(
        leave_id,
        str(user["_id"]),
        payload.leave_type,
        payload.reason,
        payload.start_date,
        payload.end_date
    )


    if leave == "not_allowed":
        raise HTTPException(
            status_code=403,
            detail="You can only update your own pending leave request"
        )


    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave not found"
        )


    return {
        "message": "Leave updated successfully",
        "leave_id": leave_id
    }



# =========================
# GET MY LEAVES
# =========================

@router.get(
    "/me",
    summary="Get My Leave Requests",
    description="Fetches the authenticated user's leave requests across the workspace. Supports filtering by approval status and relative dates."
)
def get_my_leaves(
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of records per page"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, start_date, status)"),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)"),
    status: Optional[str] = Query(None, description="Filter by approval status. Valid options: 'pending', 'approved', 'rejected'"),
    date_filter: Optional[str] = Query(None, description="Filter by relative request date. Valid options: 'today', 'yesterday', 'older'"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    **How to use filters from the frontend:**
    - To get everything: `GET /leave/me`
    - To get pending requests only: `GET /leave/me?status=pending`
    - To get older approved requests: `GET /leave/me?status=approved&date_filter=older`
    """
    user = get_authenticated_user(credentials)

    return get_my_leaves_service(
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order,
        status=status,
        date_filter=date_filter
    )

# =========================
# DELETE LEAVE
# =========================

@router.delete("/{leave_id}")
def delete_leave(
    leave_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = delete_leave_service(
        leave_id,
        str(user["_id"])
    )


    if result == "not_allowed":
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own pending leave request"
        )


    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Leave not found"
        )


    return {
        "message": "Leave deleted successfully",
        "leave_id": leave_id
    }