from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import check_owner
from src.models.attendance_policy_model import (
    CreateAttendancePolicyRequest,
    UpdateAttendancePolicyRequest,
    AttendancePolicyResponse,
)
from src.services.attendance_policy_service import (
    create_new_policy_service,
    list_workspace_policies_service,
    get_policy_service,
    update_policy_service,
    delete_policy_service,
    activate_policy_service,
)

router = APIRouter(tags=["Workspace Policy"])
bearer = HTTPBearer(auto_error=False)


def verify_user_and_ownership(workspace_id: str, credentials):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(
            status_code=403,
            detail="Only the workspace owner can manage attendance policies",
        )

    return user


@router.post("/{workspace_id}/policy", response_model=AttendancePolicyResponse)
def create_policy(
    workspace_id: str,
    payload: CreateAttendancePolicyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user = verify_user_and_ownership(workspace_id, credentials)

    policy = create_new_policy_service(
        workspace_id,
        str(user["_id"]),
        payload.model_dump(),
    )

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        name=policy["name"],
        work_start_time=policy["work_start_time"],
        work_end_time=policy["work_end_time"],
        check_in_start=policy["check_in_start"],
        check_out_start=policy["check_out_start"],
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"],
        status=policy.get("status", "inactive"),
        created_at=policy.get("created_at", datetime.now(timezone.utc)),
    )


@router.get("/{workspace_id}/policies", response_model=List[AttendancePolicyResponse])
def list_all_policies(
    workspace_id: str,
    search: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    policies = list_workspace_policies_service(
        workspace_id,
        search_term=search,
    )

    return [
        AttendancePolicyResponse(
            id=str(p["_id"]),
            workspace_id=str(p["workspace_id"]),
            name=p.get("name", "Default Policy"),
            work_start_time=p.get("work_start_time", "08:00 AM"),
            work_end_time=p.get("work_end_time", "05:00 PM"),
            check_in_start=p["check_in_start"],
            check_out_start=p.get("check_out_start", "04:30 PM"),
            late_buffer_minutes=p["late_buffer_minutes"],
            deadline_scan_minutes=p["deadline_scan_minutes"],
            annual_leave_limit=p["annual_leave_limit"],
            sick_leave_limit=p["sick_leave_limit"],
            status=p.get("status", "inactive"),
            created_at=p.get("created_at", datetime.now(timezone.utc)),
        )
        for p in policies
    ]


@router.get("/{workspace_id}/policy", response_model=AttendancePolicyResponse)
def get_current_active_policy(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    policy = get_policy_service(workspace_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="No policy configuration profile found",
        )

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        name=policy.get("name", "Active Policy"),
        work_start_time=policy.get("work_start_time", "08:00 AM"),
        work_end_time=policy.get("work_end_time", "05:00 PM"),
        check_in_start=policy["check_in_start"],
        check_out_start=policy.get("check_out_start", "04:30 PM"),
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"],
        status=policy.get("status", "inactive"),
        created_at=policy.get("created_at", datetime.now(timezone.utc)),
    )


@router.patch("/{workspace_id}/policy/{policy_id}", response_model=AttendancePolicyResponse)
def update_policy(
    workspace_id: str,
    policy_id: str,
    payload: UpdateAttendancePolicyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user = verify_user_and_ownership(workspace_id, credentials)

    policy = update_policy_service(
        workspace_id,
        policy_id,
        str(user["_id"]),
        payload.model_dump(exclude_none=True),
    )

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        name=policy["name"],
        work_start_time=policy["work_start_time"],
        work_end_time=policy["work_end_time"],
        check_in_start=policy["check_in_start"],
        check_out_start=policy["check_out_start"],
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"],
        status=policy.get("status", "inactive"),
        created_at=policy.get("created_at", datetime.now(timezone.utc)),
    )


@router.delete("/{workspace_id}/policy/{policy_id}")
def delete_policy(
    workspace_id: str,
    policy_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    verify_user_and_ownership(workspace_id, credentials)

    result = delete_policy_service(workspace_id, policy_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": "Attendance policy deleted successfully"}


@router.post("/{workspace_id}/policy/{policy_id}/activate", response_model=AttendancePolicyResponse)
def activate_policy(
    workspace_id: str,
    policy_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user = verify_user_and_ownership(workspace_id, credentials)

    policy = activate_policy_service(
        workspace_id,
        policy_id,
        str(user["_id"]),
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Attendance policy profile not found",
        )

    return AttendancePolicyResponse(
        id=str(policy["_id"]),
        workspace_id=str(policy["workspace_id"]),
        name=policy["name"],
        work_start_time=policy["work_start_time"],
        work_end_time=policy["work_end_time"],
        check_in_start=policy["check_in_start"],
        check_out_start=policy["check_out_start"],
        late_buffer_minutes=policy["late_buffer_minutes"],
        deadline_scan_minutes=policy["deadline_scan_minutes"],
        annual_leave_limit=policy["annual_leave_limit"],
        sick_leave_limit=policy["sick_leave_limit"],
        status=policy.get("status", "inactive"),
        created_at=policy.get("created_at", datetime.now(timezone.utc)),
    )