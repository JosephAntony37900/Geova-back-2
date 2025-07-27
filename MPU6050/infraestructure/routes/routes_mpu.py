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

@router.put("/mpu/sensor/{sensor_id}")
async def put_mpu_sensor(request: Request, sensor_id: int, payload: SensorMPU):
    controller = request.app.state.mpu_controller
    result = await controller.update_sensor(sensor_id, payload)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/mpu/sensor/{project_id}")
async def delete_mpu_sensor(request: Request, project_id: int):
    controller = request.app.state.mpu_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/mpu/sensor/{project_id}")
async def get_mpu_by_project_id(request: Request, project_id: int):
    controller = request.app.state.mpu_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data
    return JSONResponse(content={"error": "No se encontró inclinación para ese proyecto"}, status_code=404)

@router_ws_mpu.websocket("/mpu/sensor/ws")
async def mpu_ws(websocket: WebSocket):
    await ws_manager_mpu.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_mpu.disconnect(websocket)