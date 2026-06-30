from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import List

from src.services.auth_service import get_current_user_from_token
from src.services.workspaces_service import check_owner
from src.models.geofence_model import CreateGeofenceRequest, UpdateGeofenceRequest, GeofenceResponse
from src.services.geofence_service import (
    update_geofence_service, 
    get_geofence_service,
    create_new_geofence_service,
    list_workspaces_geofences_service,
    delete_geofence_service,
    activate_geofence_service
)

router = APIRouter(prefix="/workspaces", tags=["Workspace Geofence"])
bearer = HTTPBearer(auto_error=False)


@router.post("/{workspace_id}/geofence", response_model=GeofenceResponse)
def add_new_geofence(workspace_id: str, payload: CreateGeofenceRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can add a geofence")

    geofence = create_new_geofence_service(
        workspace_id=workspace_id,
        user_id=str(user["_id"]),
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=payload.radius_meters,
        status=payload.status
    )

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        status=geofence.get("status", "inactive"),
        created_at=geofence["created_at"]
    )


@router.get("/{workspace_id}/geofences", response_model=List[GeofenceResponse])
def list_geofences(workspace_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    geofences = list_workspaces_geofences_service(workspace_id)
    return [
        GeofenceResponse(
            id=str(g["_id"]),
            workspace_id=str(g["workspace_id"]),
            name=g["name"],
            latitude=g["latitude"],
            longitude=g["longitude"],
            radius_meters=g["radius_meters"],
            status=g.get("status", "inactive"),
            created_at=g["created_at"]
        )
        for g in geofences
    ]


@router.get("/{workspace_id}/geofence", response_model=GeofenceResponse)
def get_primary_geofence(workspace_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    geofence = get_geofence_service(workspace_id)
    if not geofence:
        raise HTTPException(404, "Geofence not found")

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        status=geofence.get("status", "inactive"),
        created_at=geofence["created_at"]
    )


@router.patch("/{workspace_id}/geofence/{geofence_id}", response_model=GeofenceResponse)
def update_geofence(workspace_id: str, geofence_id: str, payload: UpdateGeofenceRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can update geofence")

    geofence = update_geofence_service(
        workspace_id=workspace_id,
        geofence_id=geofence_id,
        user_id=str(user["_id"]),
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_meters=payload.radius_meters,
        status=payload.status
    )
    if not geofence:
        raise HTTPException(404, "Geofence not found")

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        status=geofence.get("status", "inactive"),
        created_at=geofence["created_at"]
    )


@router.delete("/{workspace_id}/geofence/{geofence_id}")
def delete_geofence(workspace_id: str, geofence_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only owner can delete geofences")

    result = delete_geofence_service(workspace_id, geofence_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": "Geofence deleted successfully"}

@router.post("/{workspace_id}/geofence/{geofence_id}/activate", response_model=GeofenceResponse)
def activate_geofence(
    workspace_id: str, 
    geofence_id: str, 
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    if not credentials:
        raise HTTPException(401, "Not authenticated")

    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(401, "Invalid token")

    if not check_owner(workspace_id, str(user["_id"])):
        raise HTTPException(403, "Only the workspace owner can switch active geofences")

    geofence = activate_geofence_service(workspace_id, geofence_id, str(user["_id"]))
    if not geofence:
        raise HTTPException(404, "Geofence not found")

    return GeofenceResponse(
        id=str(geofence["_id"]),
        workspace_id=str(geofence["workspace_id"]),
        name=geofence["name"],
        latitude=geofence["latitude"],
        longitude=geofence["longitude"],
        radius_meters=geofence["radius_meters"],
        status=geofence.get("status", "inactive"),
        created_at=geofence["created_at"]
    )