from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.attendance_service import get_workspace_attendance_service
from src.services.auth_service import get_current_user_from_token
from src.services.leave_service import get_workspace_leaves_service, approve_leave_service
from src.models.leave_model import  LeaveApprovalRequest

from src.services.workspaces_service import (
    create_workspace_service,
    add_owner_service,
    check_owner,
    get_workspaces_for_user_service,
    update_workspace_service,
    delete_workspace_service
)
from src.models.invite_model import (
    CreateInviteRequest,
    InviteResponse,
)
from src.models.geofence_model import (
    UpdateGeofenceRequest,
    GeofenceResponse,
)

from src.services.invite_service import (
    create_invite_service,
    delete_invite_service,
    get_workspace_invites_service
)

from src.services.geofence_service import (
    update_geofence_service,
    get_geofence_service
)

from src.models.workspaces_model import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest
)

from src.services.attendance_policy_service import (
    get_policy_service,
    update_policy_service
)

from src.models.attendance_policy_model import (
   
    UpdateAttendancePolicyRequest,
    AttendancePolicyResponse
)

from src.models.holiday_model import (
    CreateHolidayRequest,
    UpdateHolidayRequest,
    HolidayResponse
)

from src.services.holiday_service import (
    create_holiday_service,
    get_holidays_service,
    get_holiday_service,
    update_holiday_service,
    delete_holiday_service,
)



workspace_router = APIRouter(
    tags=["Workspace"]
)

bearer = HTTPBearer(auto_error=False)

@workspace_router.get("/me")
def get_my_workspaces(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
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
    user_id = str(user["_id"])

    workspaces = get_workspaces_for_user_service(user_id)
    return {
        "workspaces": [
            {
                "id": str(ws["_id"]),
                "workspace_name": ws["workspace_name"],
                "description": ws.get("description"),
                "status": ws.get("status"),
                "created_at": ws.get("created_at"),
                "updated_at": ws.get("updated_at")
            }
            for ws in workspaces
        ]
    }

# =========================
# CREATE WORKSPACE
# =========================
@workspace_router.post("/create")
def create_workspace(
    payload: CreateWorkspaceRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
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

    user_id = str(user["_id"])

    workspace = create_workspace_service(
        payload.workspace_name,
        payload.description
    )

    workspace_id = str(workspace["_id"])

    add_owner_service(
        workspace_id,
        user_id
    )

    return {
        "message": "Workspace created successfully",
        "workspace_id": workspace_id
    }


# =========================
# UPDATE WORKSPACE
# =========================
@workspace_router.patch("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    payload: UpdateWorkspaceRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
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

    owner = check_owner(
        workspace_id,
        str(user["_id"])
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owner can update workspace"
        )

    workspace = update_workspace_service(
        workspace_id,
        payload.workspace_name,
        payload.description,
        payload.status
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    return {
        "id": str(workspace["_id"]),
        "workspace_name": workspace["workspace_name"],
        "description": workspace.get("description"),
        "status": workspace.get("status"),
        "created_at": workspace.get("created_at"),
        "updated_at": workspace.get("updated_at")
    }

# =========================
# INVITE EMPLOYEE   
# =========================
@workspace_router.post("/{workspace_id}/invite")
def invite_employee(
    workspace_id: str,
    payload: CreateInviteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    current_user = get_current_user_from_token(
        credentials.credentials
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    owner = check_owner(
        workspace_id,
        str(current_user["_id"])
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owner can invite employees"
        )

    invite = create_invite_service(
        workspace_id,
        payload.email,
        payload.role,
        payload.expire_hours
    )

    if invite is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found"
        )

    if invite == "already_invited":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a pending invitation"
        )

    return InviteResponse(
        id=str(invite["_id"]),
        workspace_id=str(invite["workspace_id"]),
        user_id=str(invite["user_id"]),
        email=invite["email"],
        role=invite["role"],
        status=invite["status"],
        created_at=invite["created_at"],
        expires_at=invite["expires_at"]
    )

#delete invite
@workspace_router.delete("/invite/{invite_id}")
def delete_invite(invite_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = delete_invite_service(invite_id, str(user["_id"]))

    if result is None:
        raise HTTPException(404, "Invite not found")

    if result == "not_owner":
        raise HTTPException(403, "Only owner can delete invite")

    return {"message": "Invite deleted"}

#get workspace invites
@workspace_router.get("/{workspace_id}/invites")
def get_workspace_invites(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401,"Not authenticated")

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401,"Invalid token")


    if not check_owner(
        workspace_id,
        str(user["_id"])
    ):
        raise HTTPException(
            403,
            "Only owner can view invites"
        )


    return get_workspace_invites_service(
        workspace_id,
        page,
        limit
    )

#========================
# GET/UPDATE GEOFENCE
#========================
@workspace_router.get(
    "/{workspace_id}/geofence",
    response_model=GeofenceResponse
)
def get_geofence(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)

    if not user:
        raise HTTPException(401, "Invalid token")

    geofence = get_geofence_service(workspace_id)

    if not geofence:
        raise HTTPException(404, "Geofence not found")

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        created_at=geofence["created_at"]
    )

@workspace_router.patch(
    "/{workspace_id}/geofence",
    response_model=GeofenceResponse
)
def update_geofence(
    workspace_id: str,
    payload: UpdateGeofenceRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)

    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can update geofence")

    geofence = update_geofence_service(
        workspace_id,
        payload.name,
        payload.latitude,
        payload.longitude,
        payload.radius_meters
    )

    if not geofence:
        raise HTTPException(404, "Geofence not found")

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        created_at=geofence["created_at"]
    )

#========================
# GET/UPDATE ATTENDANCE POLICY
#========================
@workspace_router.get(
    "/{workspace_id}/policy",
    response_model=AttendancePolicyResponse
)
def get_policy(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)

    if not user:
        raise HTTPException(401, "Invalid token")

    policy = get_policy_service(workspace_id)

    if not policy:
        raise HTTPException(404, "Policy not found")

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        check_in_start=policy["check_in_start"],
        check_in_end=policy["check_in_end"],
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"]
    )

@workspace_router.patch("/{workspace_id}/policy", response_model=AttendancePolicyResponse)
def update_policy(
    workspace_id: str,
    payload: UpdateAttendancePolicyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)

    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can update policy")

    policy = update_policy_service(
        workspace_id,
        payload.check_in_start,
        payload.check_in_end,
        payload.late_buffer_minutes,
        payload.deadline_scan_minutes,
        payload.annual_leave_limit,
        payload.sick_leave_limit
    )

    if not policy:
        raise HTTPException(404, "Policy not found")

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        check_in_start=policy["check_in_start"],
        check_in_end=policy["check_in_end"],
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"]
    )

#========================
# GET/CREATE/UPDATE/DELETE HOLIDAYS
#========================

@workspace_router.get("/{workspace_id}/holidays")
def get_holidays(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    holidays = get_holidays_service(
        workspace_id,
        page,
        limit
    )

    return {
        "page": holidays["page"],
        "limit": holidays["limit"],
        "total": holidays["total"],
        "data": [
            {
                "id": str(h["_id"]),
                "workspace_id": str(h["workspace_id"]),
                "name": h["name"],
                "date": h["date"],
                "created_at": h["created_at"],
                "updated_at": h.get("updated_at")
            }
            for h in holidays["data"]
        ]
    }

@workspace_router.get("/{workspace_id}/holiday/{holiday_id}")
def get_holiday(
    holiday_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    holiday = get_holiday_service(
        holiday_id
    )

    if not holiday:
        raise HTTPException(404, "Holiday not found")

    return {
        "id": str(holiday["_id"]),
        "workspace_id": str(holiday["workspace_id"]),
        "name": holiday["name"],
        "date": holiday["date"],
        "created_at": holiday["created_at"],
        "updated_at": holiday.get("updated_at")
    }

@workspace_router.post(
    "/{workspace_id}/holidays",
    response_model=HolidayResponse
)
def create_holiday(
    workspace_id: str,
    payload: CreateHolidayRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(
        workspace_id,
        str(user["_id"])
    ):
        raise HTTPException(
            403,
            "Only owner can manage holidays"
        )

    holiday = create_holiday_service(
        workspace_id,
        payload.name,
        payload.date
    )

    return HolidayResponse(
        id=str(holiday["_id"]),
        workspace_id=str(holiday["workspace_id"]),
        name=holiday["name"],
        date=holiday["date"],
        created_at=holiday["created_at"],
        updated_at=holiday["updated_at"]
    )

@workspace_router.patch(
    "/holiday/{holiday_id}",
    response_model=HolidayResponse
)
def update_holiday(
    holiday_id: str,
    payload: UpdateHolidayRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    holiday = update_holiday_service(
        holiday_id,
        payload.name,
        payload.date
    )

    if not holiday:
        raise HTTPException(
            404,
            "Holiday not found"
        )

    return HolidayResponse(
        id=str(holiday["_id"]),
        workspace_id=str(holiday["workspace_id"]),
        name=holiday["name"],
        date=holiday["date"],
        created_at=holiday["created_at"],
        updated_at=holiday.get("updated_at")
    )

@workspace_router.delete(
    "/holiday/{holiday_id}"
)
def delete_holiday(
    holiday_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(401, "Invalid token")

    deleted = delete_holiday_service(
        holiday_id
    )

    if not deleted:
        raise HTTPException(
            404,
            "Holiday not found"
        )

    return {
        "message": "Holiday deleted successfully"
    }
#========================
# GET/ACCEPT-REJECT WORKSPACE LEAVES
#========================

@workspace_router.get("/leaves/{workspace_id}")
def get_workspace_leaves(
    workspace_id: str,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = get_workspace_leaves_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )

    if result == "not_owner":
        raise HTTPException(403, "Only owner can view workspace leaves")

    return result

@workspace_router.patch(
    "/leave/{leave_id}/approve"
)
def approve_leave(
    leave_id: str,
    payload: LeaveApprovalRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_current_user_from_token(
        credentials.credentials
    )

    leave = approve_leave_service(
        leave_id,
        str(user["_id"]),
        payload.status
    )

    if not leave:
        raise HTTPException(
            404,
            "Leave request not found"
        )

    return {
        "message": f"Leave {payload.status}"
    }   

# =========================
# DELETE WORKSPACE
# =========================
@workspace_router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    user = get_current_user_from_token(
        credentials.credentials
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    if not check_owner(
        workspace_id,
        str(user["_id"])
    ):
        raise HTTPException(
            status_code=403,
            detail="Only workspace owner can delete workspace"
        )

    workspace = delete_workspace_service(
        workspace_id
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return {
        "message": "Workspace deleted successfully",
        "workspace_id": workspace_id
    }

#========================
# GET WORKSPACE ATTENDANCE
#========================
@workspace_router.get("/attendance/{workspace_id}")
def get_workspace_attendance(
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

    result = get_workspace_attendance_service(
        workspace_id,
        str(user["_id"]),
        page,
        limit,
        sort_by,
        sort_order
    )

    if result == "not_owner":
        raise HTTPException(403, "Only owner can view all attendance")

    return result