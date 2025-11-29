# MPU6050/infraestructure/routes/routes_mpu.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.infraestructure.ws.ws_manager import WebSocketManager_MPU
from core.concurrency import RATE_LIMITERS
import asyncio

router_ws_mpu = APIRouter()
ws_manager_mpu = WebSocketManager_MPU()
router = APIRouter()

@router.get("/mpu/sensor")
async def get_mpu_data(request: Request, event: bool = False):
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["mpu6050"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.mpu_controller
    try:
        data = await asyncio.wait_for(
            controller.get_mpu_data(event=event),
            timeout=5.0
        )
        return data.dict() if data else {"error": "No data"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout obteniendo datos del sensor")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.put("/mpu/sensor/{sensor_id}/dual")
async def put_dual_mpu_sensor(request: Request, sensor_id: int, payload: SensorMPU):
    controller = request.app.state.mpu_controller
    result = await controller.update_dual_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=400)

@router.delete("/mpu/sensor/project/{project_id}")
async def delete_mpu_sensor_by_project(request: Request, project_id: int):
    controller = request.app.state.mpu_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/mpu/sensor/{record_id}")
async def delete_mpu_sensor_by_id(request: Request, record_id: int):
    controller = request.app.state.mpu_controller
    result = await controller.delete_sensor_by_id(record_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/mpu/sensor/{project_id}")
async def get_mpu_by_project_id(request: Request, project_id: int):
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["mpu6050"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.mpu_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        if data:
            return data
        return JSONResponse(content={"error": "No se encontró inclinación para ese proyecto"}, status_code=404)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout consultando base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_ws_mpu.websocket("/mpu/sensor/ws")
async def mpu_ws(websocket: WebSocket):
    await ws_manager_mpu.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager_mpu.disconnect(websocket)