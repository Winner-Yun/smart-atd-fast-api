from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import (
    create_workspace_service,
    check_owner,
    get_workspaces_for_user_service,
    update_workspace_service,
    delete_workspace_service
)
from src.models.workspaces_model import CreateWorkspaceRequest, UpdateWorkspaceRequest

router = APIRouter(tags=["Workspace Base"])
bearer = HTTPBearer(auto_error=False)


@router.get("/me")
def get_my_workspaces(
    search: str | None = None,
    sort: str = "asc",
    only_owner: bool = True,
    only_member: bool = False,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Validate conflicting parameters
    if only_owner and only_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameters 'only_owner' and 'only_member' cannot both be True."
        )

    user_id = str(user["_id"])

    workspaces = get_workspaces_for_user_service(
        user_id=user_id,
        search=search,
        sort=sort,
        only_owner=only_owner,
        only_member=only_member
    )

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


@router.post("/create")
def create_workspace(payload: CreateWorkspaceRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = str(user["_id"])
    workspace = create_workspace_service( user_id, payload.workspace_name, payload.description)
    workspace_id = str(workspace["_id"])

    return {"message": "Workspace created successfully", "workspace_id": workspace_id}


@router.patch("/{workspace_id}")
def update_workspace(workspace_id: str, payload: UpdateWorkspaceRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only workspace owner can update workspace")

    workspace = update_workspace_service(workspace_id, payload.workspace_name, payload.description, payload.status)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    return {
        "id": str(workspace["_id"]),
        "workspace_name": workspace["workspace_name"],
        "description": workspace.get("description"),
        "status": workspace.get("status"),
        "created_at": workspace.get("created_at"),
        "updated_at": workspace.get("updated_at")
    }


@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(status_code=403, detail="Only workspace owner can delete workspace")

    workspace = delete_workspace_service(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {"message": "Workspace deleted successfully", "workspace_id": workspace_id}