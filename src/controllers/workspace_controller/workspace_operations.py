from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional  # <-- Fixed import for Optional

from src.services.auth_service import get_current_user_from_token
from src.services.attendance_service import get_workspace_attendance_service
from src.services.leave_service import get_workspace_leaves_service, approve_leave_service
from src.models.leave_model import LeaveApprovalRequest


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Operations"]
)

bearer = HTTPBearer(auto_error=False)


def get_authenticated_user(credentials: HTTPAuthorizationCredentials):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = get_current_user_from_token(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return user


# =========================
# GET WORKSPACE LEAVES
# =========================
@router.get(
    "/leaves/{workspace_id}",
    summary="Get All Workspace Leaves (Owner Only)",
    description="Fetches leave requests for all employees in a specific workspace. Supports searching by employee details and filtering by status/date."
)
def get_workspace_leaves(
    workspace_id: str,
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of records per page"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, start_date, status)"),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)"),
    search: Optional[str] = Query(None, description="Search term for employee name, email, leave type, or reason"),
    status: Optional[str] = Query(None, description="Filter by approval status. Valid options: 'pending', 'approved', 'rejected'"),       
    date_filter: Optional[str] = Query(None, description="Filter by relative request date. Valid options: 'today', 'yesterday', 'older'"),  
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    **How to use filters from the frontend:**
    - Get everything: `GET /workspaces/leaves/{workspace_id}`
    - Search for an employee (e.g., Sok): `GET /workspaces/leaves/{workspace_id}?search=Sok`
    - Get pending leaves submitted today: `GET /workspaces/leaves/{workspace_id}?status=pending&date_filter=today`
    """
    user = get_authenticated_user(credentials)

    result = get_workspace_leaves_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order,
        search_term=search,
        status=status,            
        date_filter=date_filter   
    )

    if result == "not_owner":
        raise HTTPException(
            status_code=403,
            detail="Only owner can view workspace leaves"
        )

    return result


# =========================
# APPROVE / REJECT LEAVE
# =========================
@router.patch(
    "/leave/{leave_id}/approve",
    summary="Approve or Reject a Leave Request",
    description="Allows a workspace owner to update the status of an employee's pending leave request."
)
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


# =========================
# GET WORKSPACE ATTENDANCE
# =========================
@router.get(
    "/attendance/{workspace_id}",
    summary="Get All Workspace Attendance (Owner Only)",
    description="Fetches attendance logs for all employees in a specific workspace. Supports searching by employee details and filtering by attendance status."
)
def get_workspace_attendance(
    workspace_id: str,
    page: int = Query(1, description="Page number for pagination"),
    limit: int = Query(10, description="Number of records per page"),
    sort_by: str = Query("date", description="Field to sort by (date, created_at, check_in, status)"),
    sort_order: str = Query("desc", description="Sort direction (asc or desc)"),
    search: Optional[str] = Query(None, description="Search term for employee name or email"),
    status: Optional[str] = Query(None, description="Filter by attendance status. Valid options: 'present', 'late', 'absent'"),       
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    **How to use filters from the frontend:**
    - Get everything: `GET /workspaces/attendance/{workspace_id}`
    - Search for an employee (e.g., Chan): `GET /workspaces/attendance/{workspace_id}?search=chan`
    - Filter to see only late employees: `GET /workspaces/attendance/{workspace_id}?status=late`
    - Search for late employees named Chan: `GET /workspaces/attendance/{workspace_id}?search=chan&status=late`
    """
    user = get_authenticated_user(credentials)

    result = get_workspace_attendance_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order,
        search_term=search,
        status=status 
    )

    if result == "not_owner":
        raise HTTPException(
            status_code=403,
            detail="Only owner can view workspace attendance"
        )

    return result