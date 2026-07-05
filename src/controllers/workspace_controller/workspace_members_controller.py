from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import check_owner
from src.models.workspace_members_model import UpdateMemberStatusRequest, WorkspaceMemberListResponse
from src.services.workspace_members_service import (
    get_workspace_members_service,
    update_member_status_service,
    remove_member_service
)

router = APIRouter(tags=["Workspace Members"])
bearer = HTTPBearer(auto_error=False)


@router.get("/{workspace_id}/members", response_model=WorkspaceMemberListResponse)
def get_workspace_members(
    workspace_id: str,
    search: str | None = None,
    sort: str = "asc",
    include_pending: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Optional: You can check if the requester is at least a member before showing the list
    # For now, it fetches the list based on your parameters
    members = get_workspace_members_service(
        workspace_id=workspace_id,
        search=search,
        sort_order=sort,
        include_pending=include_pending
    )

    return WorkspaceMemberListResponse(
        workspace_id=workspace_id,
        total=len(members),
        members=members
    )


@router.patch("/{workspace_id}/members/{user_id}/status")
def update_member_status(
    workspace_id: str,
    user_id: str,
    payload: UpdateMemberStatusRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    current_user = get_current_user_from_token(credentials.credentials)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # MUST BE OWNER TO SUSPEND/UPDATE MEMBERS
    if not check_owner(workspace_id, str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="Only workspace owner can update member status")

    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot suspend themselves")

    success = update_member_status_service(workspace_id, user_id, payload.status)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found or cannot modify owner")

    return {"message": f"Member status updated to {payload.status}"}


@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(
    workspace_id: str,
    user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    current_user = get_current_user_from_token(credentials.credentials)
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # MUST BE OWNER TO REMOVE MEMBERS
    if not check_owner(workspace_id, str(current_user["_id"])):
        raise HTTPException(status_code=403, detail="Only workspace owner can remove members")

    if str(current_user["_id"]) == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves")

    success = remove_member_service(workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found or cannot remove owner")

    return {"message": "Member removed from workspace successfully"}