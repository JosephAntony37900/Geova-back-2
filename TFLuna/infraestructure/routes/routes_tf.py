# TFLuna/infraestructure/routes/routes_tf.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.infraestructure.ws.ws_manager import WebSocketManager
from core.concurrency import RATE_LIMITERS
import asyncio

router_ws_tf = APIRouter()
ws_manager = WebSocketManager()
router = APIRouter()

@router.get("/tfluna/sensor")
async def get_sensor(request: Request, event: bool = False):
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["tfluna"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.tf_controller
    try:
        data = await asyncio.wait_for(
            controller.get_tf_data(event=event),
            timeout=5.0
        )
        return data.dict() if data else {"error": "No data"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout obteniendo datos del sensor")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tfluna/sensor")
async def post_sensor(request: Request, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.put("/tfluna/sensor/{sensor_id}")
async def put_sensor(request: Request, sensor_id: int, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.update_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.put("/tfluna/sensor/{sensor_id}/dual")
async def put_dual_sensor(request: Request, sensor_id: int, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.update_dual_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=400)

@router.delete("/tfluna/sensor/project/{project_id}")
async def delete_sensor_by_project(request: Request, project_id: int):
    controller = request.app.state.tf_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/tfluna/sensor/{record_id}")
async def delete_sensor_by_id(request: Request, record_id: int):
    controller = request.app.state.tf_controller
    result = await controller.delete_sensor_by_id(record_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/tfluna/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["tfluna"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.tf_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        if data:
            return data
        return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout consultando base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_ws_tf.websocket("/tfluna/sensor/ws")
async def tf_luna_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)