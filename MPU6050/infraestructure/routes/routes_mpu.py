# MPU6050/infraestructure/routes/routes_mpu.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.infraestructure.ws.ws_manager import WebSocketManager_MPU

router_ws_mpu = APIRouter()
ws_manager_mpu = WebSocketManager_MPU()
router = APIRouter()

@router.get("/mpu/sensor")
async def get_mpu_data(request: Request, event: bool = False):
    controller = request.app.state.mpu_controller
    data = await controller.get_mpu_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router.post("/mpu/sensor")
async def post_mpu_sensor(request: Request, payload: SensorMPU):
    controller = request.app.state.mpu_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.get("/mpu/sensor/{project_id}")
async def get_mpu_by_project_id(request: Request, project_id: int):
    controller = request.app.state.mpu_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data.dict()
    return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)

@router_ws_mpu.websocket("/mpu/sensor/ws")
async def mpu_ws(websocket: WebSocket):
    await ws_manager_mpu.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_mpu.disconnect(websocket)