from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import check_owner
from src.models.holiday_model import CreateHolidayRequest, HolidayConfigResponse, UpdateHolidayRequest, HolidayResponse, UpdateHolidayConfigRequest
from src.services.holiday_service import (
    create_holiday_service,
    get_holidays_service,
    get_holiday_service,
    update_holiday_service,
    delete_holiday_service,
    get_holiday_config_service,
    update_holiday_config_service
)

router = APIRouter(tags=["Workspace Holidays"])
bearer = HTTPBearer(auto_error=False)

# =========================
# CONFIGURATION ENDPOINTS
# =========================
@router.get("/{workspace_id}/holiday-config", response_model=HolidayConfigResponse)
def get_holiday_config(workspace_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    config = get_holiday_config_service(workspace_id)
    return HolidayConfigResponse(
        workspace_id=str(config["workspace_id"]),
        include_public_holidays=config["include_public_holidays"],
        include_weekend=config["include_weekend"],
        updated_at=config["updated_at"]
    )

@router.patch("/{workspace_id}/holiday-config", response_model=HolidayConfigResponse)
def update_holiday_config(workspace_id: str, payload: UpdateHolidayConfigRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only the workspace owner can update holiday configurations")

    config = update_holiday_config_service(
        workspace_id, 
        payload.include_public_holidays, 
        payload.include_weekend
    )
    return HolidayConfigResponse(
        workspace_id=str(config["workspace_id"]),
        include_public_holidays=config["include_public_holidays"],
        include_weekend=config["include_weekend"],
        updated_at=config["updated_at"]
    )


@router.get("/{workspace_id}/holidays")
def get_holidays(
    workspace_id: str, 
    page: int = 1, 
    limit: int = 10, 
    search: str = None,  # <-- 1. Added optional search query parameter
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    # 2. Pass the search query parameter into the updated service
    holidays = get_holidays_service(workspace_id, page, limit, search_term=search)
    
    return {
        "page": holidays["page"],
        "limit": holidays["limit"],
        "total": holidays["total"],
        "data": [
            {
                "id": str(h["_id"]),
                "workspace_id": str(h["workspace_id"]),
                "name": h["name"],
                "date": h["date"],
                "created_at": h["created_at"],
                "updated_at": h.get("updated_at")
            }
            for h in holidays["data"]
        ]
    }


@router.get("/{workspace_id}/holiday/{holiday_id}")
def get_holiday(holiday_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    holiday = get_holiday_service(holiday_id)
    if not holiday:
        raise HTTPException(404, "Holiday not found")

    return {
        "id": str(holiday["_id"]),
        "workspace_id": str(holiday["workspace_id"]),
        "name": holiday["name"],
        "date": holiday["date"],
        "created_at": holiday["created_at"],
        "updated_at": holiday.get("updated_at")
    }


@router.post("/{workspace_id}/holidays", response_model=HolidayResponse)
def create_holiday(workspace_id: str, payload: CreateHolidayRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can manage holidays")

    holiday = create_holiday_service(workspace_id, payload.name, payload.date)
    return HolidayResponse(
        id=str(holiday["_id"]),
        workspace_id=str(holiday["workspace_id"]),
        name=holiday["name"],
        date=holiday["date"],
        created_at=holiday["created_at"],
        updated_at=holiday["updated_at"]
    )


@router.patch("/holiday/{holiday_id}", response_model=HolidayResponse)
def update_holiday(holiday_id: str, payload: UpdateHolidayRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    holiday = update_holiday_service(holiday_id, payload.name, payload.date)
    if not holiday:
        raise HTTPException(404, "Holiday not found")

    return HolidayResponse(
        id=str(holiday["_id"]),
        workspace_id=str(holiday["workspace_id"]),
        name=holiday["name"],
        date=holiday["date"],
        created_at=holiday["created_at"],
        updated_at=holiday.get("updated_at")
    )


@router.delete("/holiday/{holiday_id}")
def delete_holiday(holiday_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    deleted = delete_holiday_service(holiday_id)
    if not deleted:
        raise HTTPException(404, "Holiday not found")

    return {"message": "Holiday deleted successfully"}