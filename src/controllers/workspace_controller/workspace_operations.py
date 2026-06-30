from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.attendance_service import get_workspace_attendance_service
from src.services.leave_service import get_workspace_leaves_service, approve_leave_service
from src.models.leave_model import LeaveApprovalRequest


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Operations"]
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



@router.get("/leaves/{workspace_id}")
def get_workspace_leaves(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = get_workspace_leaves_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )


    if result == "not_owner":
        raise HTTPException(
            status_code=403,
            detail="Only owner can view workspace leaves"
        )


    return result



@router.patch("/leave/{leave_id}/approve")
def approve_leave(
    leave_id: str,
    payload: LeaveApprovalRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    leave = approve_leave_service(
        leave_id,
        str(user["_id"]),
        payload.status
    )


    if not leave:
        raise HTTPException(
            status_code=404,
            detail="Leave request not found"
        )


    return {
        "message": f"Leave {payload.status}"
    }



@router.get("/attendance/{workspace_id}")
def get_workspace_attendance(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "date",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = get_workspace_attendance_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )


    if result == "not_owner":
        raise HTTPException(
            status_code=403,
            detail="Only owner can view all attendance"
        )


    return result