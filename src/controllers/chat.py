from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth import get_current_user_from_token
from src.services.chat import (
    check_member,
    send_message,
    get_messages,
    read_message,
    edit_message,
    delete_message
)

from src.models.chat import CreateMessageRequest


chat_router = APIRouter(tags=["Chat"])
bearer = HTTPBearer(auto_error=False)


# =========================
# SEND MESSAGE
# =========================
@chat_router.post("/{workspace_id}")
def send_message_api(
    workspace_id: str,
    payload: CreateMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_member(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Not workspace member")

    msg = send_message(workspace_id, str(user["_id"]), payload.message)

    return {"id": str(msg["_id"])}


# =========================
# GET MESSAGES
# =========================
@chat_router.get("/{workspace_id}")
def get_messages_api(
    workspace_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_member(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Not workspace member")

    return get_messages(workspace_id, str(user["_id"]))


# =========================
# READ MESSAGE
# =========================
@chat_router.patch("/{workspace_id}/{message_id}/read")
def read_message_api(
    workspace_id: str,
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = read_message(workspace_id, message_id, str(user["_id"]))

    if not result:
        raise HTTPException(403, "Not workspace member")

    return {"message": "read"}


# =========================
# EDIT MESSAGE
# =========================
@chat_router.patch("/{workspace_id}/{message_id}/edit")
def edit_message_api(
    workspace_id: str,
    message_id: str,
    payload: CreateMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    msg = edit_message(
        workspace_id,
        message_id,
        str(user["_id"]),
        payload.message
    )

    if not msg:
        raise HTTPException(404, "Message not found or not allowed")

    return {"message": "edited"}


# =========================
# UNSEND MESSAGE (DELETE)
# =========================
@chat_router.delete("/{workspace_id}/{message_id}")
def delete_message_api(
    workspace_id: str,
    message_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    result = delete_message(workspace_id, message_id, str(user["_id"]))

    if not result:
        raise HTTPException(404, "Message not found or not allowed")

    return {"message": "unsent"}