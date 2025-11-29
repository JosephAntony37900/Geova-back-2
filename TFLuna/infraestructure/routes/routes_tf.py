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
    """Obtiene lectura actual del sensor TF-Luna."""
    if not await RATE_LIMITERS["tfluna"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones al sensor TF-Luna, intente más tarde")
    
    controller = request.app.state.tf_controller
    try:
        data = await asyncio.wait_for(
            controller.get_tf_data(event=event),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data.dict()}
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "El sensor TF-Luna no está disponible o no hay datos"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: El sensor TF-Luna tardó demasiado en responder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer sensor TF-Luna: {str(e)}")

@router.post("/tfluna/sensor")
async def post_sensor(request: Request, payload: SensorTF):
    """Guarda una nueva medición del sensor TF-Luna."""
    controller = request.app.state.tf_controller
    try:
        result = await controller.create_sensor(payload)
        if result.get("success", True) and "error" not in result.get("msg", "").lower():
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al guardar medición TF-Luna: {str(e)}"}
        )

@router.put("/tfluna/sensor/{sensor_id}")
async def put_sensor(request: Request, sensor_id: int, payload: SensorTF):
    """Actualiza una medición existente del sensor TF-Luna."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.tf_controller
    try:
        result = await controller.update_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al actualizar medición TF-Luna: {str(e)}"}
        )

@router.put("/tfluna/sensor/{sensor_id}/dual")
async def put_dual_sensor(request: Request, sensor_id: int, payload: SensorTF):
    """Completa una medición dual del sensor TF-Luna."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.tf_controller
    try:
        result = await controller.update_dual_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al completar medición dual TF-Luna: {str(e)}"}
        )

@router.delete("/tfluna/sensor/project/{project_id}")
async def delete_sensor_by_project(request: Request, project_id: int):
    """Elimina todas las mediciones de TF-Luna de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    controller = request.app.state.tf_controller
    try:
        result = await controller.delete_sensor(project_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar mediciones TF-Luna: {str(e)}"}
        )

@router.delete("/tfluna/sensor/{record_id}")
async def delete_sensor_by_id(request: Request, record_id: int):
    """Elimina una medición específica de TF-Luna por ID."""
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del registro debe ser un número positivo")
    
    controller = request.app.state.tf_controller
    try:
        result = await controller.delete_sensor_by_id(record_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar registro TF-Luna: {str(e)}"}
        )

@router.get("/tfluna/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    """Obtiene las mediciones de TF-Luna de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["tfluna"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.tf_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No se encontraron mediciones TF-Luna para el proyecto {project_id}"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La consulta tardó demasiado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar mediciones: {str(e)}")

@router_ws_tf.websocket("/tfluna/sensor/ws")
async def tf_luna_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)