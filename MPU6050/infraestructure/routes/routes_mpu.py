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
    """Obtiene lectura actual del sensor MPU6050 (inclinómetro)."""
    if not await RATE_LIMITERS["mpu6050"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones al sensor MPU6050, intente más tarde")
    
    controller = request.app.state.mpu_controller
    try:
        data = await asyncio.wait_for(
            controller.get_mpu_data(event=event),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data.dict()}
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "El sensor MPU6050 no está disponible o no hay datos"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: El sensor MPU6050 tardó demasiado en responder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer sensor MPU6050: {str(e)}")

@router.post("/mpu/sensor")
async def post_mpu_sensor(request: Request, payload: SensorMPU):
    """Guarda una nueva medición del sensor MPU6050."""
    controller = request.app.state.mpu_controller
    try:
        result = await controller.create_sensor(payload)
        if result.get("success", True) and "error" not in result.get("msg", "").lower():
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al guardar medición MPU6050: {str(e)}"}
        )

@router.put("/mpu/sensor/{sensor_id}")
async def put_mpu_sensor(request: Request, sensor_id: int, payload: SensorMPU):
    """Actualiza una medición existente del sensor MPU6050."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.mpu_controller
    try:
        result = await controller.update_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al actualizar medición MPU6050: {str(e)}"}
        )

@router.put("/mpu/sensor/{sensor_id}/dual")
async def put_dual_mpu_sensor(request: Request, sensor_id: int, payload: SensorMPU):
    """Completa una medición dual del sensor MPU6050."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.mpu_controller
    try:
        result = await controller.update_dual_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al completar medición dual MPU6050: {str(e)}"}
        )

@router.delete("/mpu/sensor/project/{project_id}")
async def delete_mpu_sensor_by_project(request: Request, project_id: int):
    """Elimina todas las mediciones de MPU6050 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    controller = request.app.state.mpu_controller
    try:
        result = await controller.delete_sensor(project_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar mediciones MPU6050: {str(e)}"}
        )

@router.delete("/mpu/sensor/{record_id}")
async def delete_mpu_sensor_by_id(request: Request, record_id: int):
    """Elimina una medición específica de MPU6050 por ID."""
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del registro debe ser un número positivo")
    
    controller = request.app.state.mpu_controller
    try:
        result = await controller.delete_sensor_by_id(record_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar registro MPU6050: {str(e)}"}
        )

@router.get("/mpu/sensor/{project_id}")
async def get_mpu_by_project_id(request: Request, project_id: int):
    """Obtiene las mediciones de inclinación (MPU6050) de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["mpu6050"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.mpu_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No se encontraron mediciones de inclinación para el proyecto {project_id}"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La consulta tardó demasiado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar mediciones: {str(e)}")

@router_ws_mpu.websocket("/mpu/sensor/ws")
async def mpu_ws(websocket: WebSocket):
    await ws_manager_mpu.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager_mpu.disconnect(websocket)