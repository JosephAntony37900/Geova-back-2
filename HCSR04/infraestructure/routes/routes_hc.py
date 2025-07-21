# HCSR04/infraestructure/routes/routes_hc.py
from fastapi import APIRouter, Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from HCSR04.infraestructure.ws.ws_manager import WebSocketManager_HC


router = APIRouter()
router_ws_hc = APIRouter()
ws_manager_hc = WebSocketManager_HC()

@router.get("/hc-sensor")
async def get_hc_sensor(request: Request, event: bool = True):
    controller = request.app.state.hc_controller
    data = await controller.get_hc_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router_ws_hc.websocket("/ws/hc")
async def hc_ws(websocket: WebSocket):
    await ws_manager_hc.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_hc.disconnect(websocket)
