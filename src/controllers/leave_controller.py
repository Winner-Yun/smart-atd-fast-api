from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

leave_router = APIRouter(
    tags=["Leave"]
)

bearer = HTTPBearer(auto_error=False)


# =========================
# CREATE LEAVE
# =========================
@leave_router.post(
    "/{workspace_id}/leave",
    response_model=LeaveResponse
)
def create_leave(
    workspace_id: str,
    payload: CreateLeaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

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
@leave_router.patch("/{leave_id}")
def update_leave(
    leave_id: str,
    payload: CreateLeaveRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

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
@leave_router.get("/me")
def get_my_leaves(
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    return get_my_leaves_service(
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )


# =========================
# DELETE LEAVE
# =========================
@leave_router.delete("/{leave_id}")
def delete_leave(
    leave_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

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