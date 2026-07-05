from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import check_owner
from src.models.invite_model import CreateInviteRequest, InviteResponse
from src.services.invite_service import create_invite_service, delete_invite_service, get_workspace_invites_service

router = APIRouter(tags=["Workspace Invites"])
bearer = HTTPBearer(auto_error=False)


@router.post("/{workspace_id}/invite", response_model=InviteResponse)
def invite_employee(workspace_id: str, payload: CreateInviteRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, detail="Not authenticated")

    current_user = get_current_user_from_token(credentials.credentials)
    if not current_user:
        raise HTTPException(401, detail="Invalid token")

    if not check_owner(workspace_id, str(current_user["_id"])):
        raise HTTPException(403, detail="Only workspace owner can invite employees")

    invite = create_invite_service(workspace_id, payload.email, payload.role, payload.expire_hours)
    if invite is None:
        raise HTTPException(404, detail="User account not found")
    if invite == "already_invited":
        raise HTTPException(400, detail="User already has a pending invitation")

    return InviteResponse(
        id=str(invite["_id"]),
        workspace_id=str(invite["workspace_id"]),
        user_id=str(invite["user_id"]),
        email=invite["email"],
        position=invite["position"],
        role=invite["role"],
        status=invite["status"],
        created_at=invite["created_at"],
        expires_at=invite["expires_at"]
    )


@router.get("/{workspace_id}/invites")
def get_workspace_invites(workspace_id: str, page: int = 1, limit: int = 10, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can view invites")

    return get_workspace_invites_service(workspace_id, page, limit)


@router.delete("/invite/{invite_id}")
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