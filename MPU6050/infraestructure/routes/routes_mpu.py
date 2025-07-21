# MPU6050/infraestructure/routes/routes_mpu.py
from fastapi import APIRouter, Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from MPU6050.infraestructure.ws.ws_manager import WebSocketManager_MPU

router = APIRouter()
router_ws_mpu = APIRouter()
ws_manager_mpu = WebSocketManager_MPU()

@router.get("/mpu")
async def get_mpu_data(request: Request, event: bool = False):
    controller = request.app.state.mpu_controller
    data = await controller.get_mpu_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router_ws_mpu.websocket("/ws/mpu")
async def mpu_ws(websocket: WebSocket):
    await ws_manager_mpu.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_mpu.disconnect(websocket)