from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.websocket.ws_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/sensores")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Puedes usarlo como "ping"
    except WebSocketDisconnect:
        manager.disconnect(websocket)
