from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token

from src.services.chat_service import (
    check_member,
    send_message,
    get_messages,
    read_message,
    edit_message,
    delete_message
)

from src.models.chat_model import CreateMessageRequest


router = APIRouter(
    tags=["Chat"]
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



# =========================
# SEND MESSAGE
# =========================

@router.post("/{workspace_id}")
def send_message_api(
    workspace_id: str,
    payload: CreateMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    user_id = str(user["_id"])


    if not check_member(workspace_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Not workspace member"
        )


    msg = send_message(
        workspace_id,
        user_id,
        payload.message
    )


    return {
        "id": str(msg["_id"])
    }



# =========================
# GET MESSAGES
# =========================

@router.get("/{workspace_id}")
def get_messages_api(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    user_id = str(user["_id"])


    if not check_member(workspace_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Not workspace member"
        )


    return get_messages(
        workspace_id,
        user_id
    )



# =========================
# READ MESSAGE
# =========================

@router.patch("/{workspace_id}/{message_id}/read")
def read_message_api(
    workspace_id: str,
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = read_message(
        workspace_id,
        message_id,
        str(user["_id"])
    )


    if not result:
        raise HTTPException(
            status_code=403,
            detail="Not workspace member"
        )


    return {
        "message": "read"
    }



# =========================
# EDIT MESSAGE
# =========================

@router.patch("/{workspace_id}/{message_id}/edit")
def edit_message_api(
    workspace_id: str,
    message_id: str,
    payload: CreateMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    msg = edit_message(
        workspace_id,
        message_id,
        str(user["_id"]),
        payload.message
    )


    if not msg:
        raise HTTPException(
            status_code=404,
            detail="Message not found or not allowed"
        )


    return {
        "message": "edited"
    }



# =========================
# UNSEND MESSAGE (DELETE)
# =========================

@router.delete("/{workspace_id}/{message_id}")
def delete_message_api(
    workspace_id: str,
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    result = delete_message(
        workspace_id,
        message_id,
        str(user["_id"])
    )


    if not result:
        raise HTTPException(
            status_code=404,
            detail="Message not found or not allowed"
        )


    return {
        "message": "unsent"
    }