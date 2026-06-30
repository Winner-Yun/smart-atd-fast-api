from fastapi import APIRouter, Depends, HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.services.auth_service import get_current_user_from_token
from src.services.invite_service import (
    accept_invite_service,
    get_my_invites_service,
    reject_invite_service
)


invite_router = APIRouter(tags=["Invite"])
bearer = HTTPBearer(auto_error=False)

#========================
# accept invite
#========================
@invite_router.post("/invite/{invite_id}/accept")
def accept_invite(
    invite_id: str,
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

    result = accept_invite_service(
        invite_id,
        str(current_user["_id"])
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite does not belong to you"
        )

    if result == "already_processed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite already processed"
        )

    if result == "already_member":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a workspace member"
        )

    return {
        "message": "Invite accepted successfully",
        "workspace_id": str(result["workspace_id"]),
        "role": result["role"]
    }

#reject invite

@invite_router.patch("/{invite_id}/reject")
def reject_invite(invite_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = reject_invite_service(invite_id, str(user["_id"]))

    if result is None:
        raise HTTPException(404, "Invite not found")

    if result == "forbidden":
        raise HTTPException(403, "Not your invite")

    if result == "already_processed":
        raise HTTPException(400, "Already processed")

    return {"message": "Invite rejected"}

#get my invites

@invite_router.get("/me")
def get_my_invites(
    page: int = 1,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    return get_my_invites_service(str(user["_id"]), page, limit)