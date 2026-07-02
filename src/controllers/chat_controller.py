from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

from src.services.auth_service import get_current_user_from_token
from src.services.chat_service import (
    get_or_create_conversation,
    get_user_conversations,
    save_new_message,
    get_messages_by_conversation,
    modify_message_text,
    soft_delete_message,
    mark_message_as_read,
    conversation_col
)
from src.models.chat_model import CreateMessageRequest, CreateConversationRequest, EditMessageRequest


router = APIRouter(tags=["Chat"])
bearer = HTTPBearer(auto_error=False)


def get_authenticated_user(credentials: HTTPAuthorizationCredentials):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization headers.")
        
    user = get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has expired or token is invalid.")
        
    return user


# ==============================================================================
# REALTIME CONNECTION DISPATCH MANAGER
# ==============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(jsonable_encoder(message))
                except Exception:
                    pass

    async def broadcast_to_channel_members(self, message: dict, conversation_id: str):
        conv = conversation_col().find_one({"_id": ObjectId(conversation_id)})
        if not conv:
            return
        for participant in conv.get("participants", []):
            await self.send_to_user(message, str(participant))


manager = ConnectionManager()


# ==============================================================================
# REALTIME WEBSOCKET HUB (Query Params Isolation)
# ==============================================================================

@router.websocket("/ws")
async def unified_websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(...),
    workspace_id: str = Query(...)
):
    user = get_current_user_from_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = str(user["_id"])
    await manager.connect(user_id, websocket)

    try:
        while True:
            packet = await websocket.receive_json()
            event = packet.get("event")
            payload = packet.get("data", {})
            conv_id = payload.get("conversation_id")

            if not conv_id:
                continue

            if event == "send_message":
                text = payload.get("message")
                msg = save_new_message(conv_id, workspace_id, user_id, text)
                
                if msg:
                    await manager.broadcast_to_channel_members({
                        "event": "new_message",
                        "data": {
                            "id": str(msg["_id"]),
                            "conversation_id": conv_id,
                            "sender_id": user_id,
                            "message": msg["message"],
                            "created_at": msg["created_at"].isoformat()
                        }
                    }, conv_id)

            elif event == "typing":
                await manager.broadcast_to_channel_members({
                    "event": "typing",
                    "data": {
                        "conversation_id": conv_id,
                        "user_id": user_id,
                        "is_typing": bool(payload.get("is_typing", False))
                    }
                }, conv_id)

            elif event == "message_read":
                msg_id = payload.get("message_id")
                if mark_message_as_read(msg_id, user_id):
                    await manager.broadcast_to_channel_members({
                        "event": "message_read",
                        "data": {
                            "conversation_id": conv_id,
                            "message_id": msg_id,
                            "user_id": user_id
                        }
                    }, conv_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)


# ==============================================================================
# REST API LEDGER & CHANNEL MANAGEMENT ENDPOINTS (Header Driven)
# ==============================================================================

@router.post("/conversations")
def api_initialize_room(
    payload: CreateConversationRequest, 
    workspace_id: str = Header(..., alias="Workspace-Id"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_authenticated_user(credentials)
    
    room, error_msg = get_or_create_conversation(str(user["_id"]), workspace_id, payload.model_dump())
    if error_msg:
        raise HTTPException(status_code=403, detail=error_msg)
        
    return {
        "id": str(room["_id"]),
        "workspace_id": str(room["workspace_id"]),
        "type": room["type"],
        "name": room.get("name", "Direct Message"),
        "participants": [str(p) for p in room["participants"]]
    }


@router.get("/conversations")
def api_list_user_rooms(
    workspace_id: str = Header(..., alias="Workspace-Id"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_authenticated_user(credentials)
    return get_user_conversations(str(user["_id"]), workspace_id)


@router.get("/conversations/{conversation_id}/messages")
def api_fetch_room_ledger(
    conversation_id: str, 
    workspace_id: str = Header(..., alias="Workspace-Id"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_authenticated_user(credentials)
    history = get_messages_by_conversation(conversation_id, workspace_id, str(user["_id"]))
    
    if history is None:
        raise HTTPException(status_code=403, detail="Access denied. Channel constraints violated.")
        
    return history


@router.patch("/messages/{message_id}")
def api_update_message_text(
    message_id: str,
    payload: EditMessageRequest,
    workspace_id: str = Header(..., alias="Workspace-Id"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_authenticated_user(credentials)
    updated = modify_message_text(message_id, workspace_id, str(user["_id"]), payload.new_message)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Message not found, or modification permissions denied.")
        
    return {"status": "success", "message": "Message successfully updated."}


@router.delete("/messages/{message_id}")
def api_delete_message_record(
    message_id: str,
    workspace_id: str = Header(..., alias="Workspace-Id"),
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
):
    user = get_authenticated_user(credentials)
    success = soft_delete_message(message_id, workspace_id, str(user["_id"]))
    
    if not success:
        raise HTTPException(status_code=404, detail="Message not found, or retraction permissions denied.")
        
    return {"status": "success", "message": "Message successfully retracted."}