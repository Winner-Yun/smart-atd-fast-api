from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token

from src.services.notification_service import (
    create_notification_service,
    get_my_notifications_service,
    is_member,
    read_notification_service
)

from src.services.workspaces_service import check_owner

from src.models.notification_model import (
    CreateNotificationRequest,
    NotificationResponse
)


router = APIRouter(
    tags=["Notification"]
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
# CREATE NOTIFICATION
# =========================

@router.post("/")
def create_notification(
    payload: CreateNotificationRequest,
    workspace_id: str = Header(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    user_id = str(user["_id"])


    if not check_owner(workspace_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="Only admin can send notification"
        )


    # validate target

    if payload.target == "global":
        pass


    elif payload.target.startswith("personal:"):

        target_user = payload.target.split(":")[1]


        if not is_member(workspace_id, target_user):
            raise HTTPException(
                status_code=400,
                detail="Target user not in workspace"
            )


    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid target format"
        )



    notification = create_notification_service(
        workspace_id,
        user_id,
        payload.title,
        payload.message,
        payload.type,
        payload.target
    )


    return NotificationResponse(
        id=str(notification["_id"]),
        workspace_id=str(notification["workspace_id"]),
        title=notification["title"],
        message=notification["message"],
        type=notification["type"],
        target=notification["target"],
        is_read=False,
        created_at=str(notification["created_at"])
    )



# =========================
# GET NOTIFICATIONS
# =========================

@router.get("/")
def get_notifications(
    workspace_id: str = Header(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    return get_my_notifications_service(
        workspace_id,
        str(user["_id"])
    )



# =========================
# READ NOTIFICATION
# =========================

@router.patch("/{notification_id}/read")
def read_notification(
    notification_id: str,
    workspace_id: str = Header(...),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):

    user = get_authenticated_user(credentials)


    user_id = str(user["_id"])


    result = read_notification_service(
        notification_id,
        user_id,
        workspace_id
    )


    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )


    if result == "not_member":
        raise HTTPException(
            status_code=403,
            detail="Not workspace member"
        )


    if result == "forbidden":
        raise HTTPException(
            status_code=403,
            detail="This notification is not for you"
        )


    return {
        "message": "Notification read"
    }