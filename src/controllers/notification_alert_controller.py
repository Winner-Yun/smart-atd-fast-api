from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.notification_alert_service import (
    create_alert_service,
    get_alerts_service,
    read_alert_service,
    delete_alert_service
)
from src.models.notification_alert_model import (
    CreateNotificationAlertRequest,
    NotificationAlertResponse
)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/alerts",
    tags=["Notification Alerts"]
)
bearer = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    return user


# =========================
# SAVE/CREATE ALERT (Now uses Bearer Token for User ID!)
# =========================
@router.post("/", response_model=NotificationAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    workspace_id: str,
    payload: CreateNotificationAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    # Extract user_id directly from the Authorized Bearer Token
    user_id = str(current_user["_id"])

    result = create_alert_service(
        workspace_id=workspace_id,
        user_id=user_id, # Securely passed from backend auth
        title=payload.title,
        message=payload.message,
        type=payload.type
    )

    if result == "not_member":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not a member of this workspace"
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input details"
        )

    return NotificationAlertResponse(
        id=str(result["_id"]),
        workspace_id=str(result["workspace_id"]),
        user_id=str(result["user_id"]),
        title=result["title"],
        message=result["message"],
        type=result["type"],
        is_read=result["is_read"],
        created_at=str(result["created_at"])
    )


# =========================
# GET ALERTS
# =========================
@router.get("/", response_model=list[NotificationAlertResponse])
def get_alerts(
    workspace_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    result = get_alerts_service(workspace_id, user_id)

    if result == "not_member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    return result


# =========================
# MARK ALERT AS READ
# =========================
@router.patch("/{alert_id}/read")
def read_alert(
    workspace_id: str,
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    result = read_alert_service(workspace_id, alert_id, user_id)

    if result == "not_member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return {
        "message": "Alert marked as read"}


# =========================
# DELETE ALERT
# =========================
@router.delete("/{alert_id}")
def delete_alert(
    workspace_id: str,
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user["_id"])
    result = delete_alert_service(workspace_id, alert_id, user_id)

    if result == "not_member":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    return {"message": "Alert deleted successfully"}