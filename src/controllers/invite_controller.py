from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.invite_service import (
    accept_invite_service,
    get_my_invites_service,
    reject_invite_service
)


router = APIRouter(tags=["Invite"])

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



# ========================
# ACCEPT INVITE
# ========================

@router.post("{invite_id}/accept")
def accept_invite(
    invite_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    current_user = get_authenticated_user(credentials)


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



# ========================
# REJECT INVITE
# ========================

@router.patch("/{invite_id}/reject")
def reject_invite(
    invite_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = reject_invite_service(
        invite_id,
        str(user["_id"])
    )


    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )


    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your invite"
        )


    if result == "already_processed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already processed"
        )


    return {
        "message": "Invite rejected"
    }



# ========================
# GET MY INVITES
# ========================

@router.get("/me")
def get_my_invites(
    page: int = 1,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    return get_my_invites_service(
        str(user["_id"]),
        page,
        limit
    )