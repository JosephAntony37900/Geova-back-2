# IMX477/infraestructure/routes/routes_imx.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.ws.ws_manager import WebSocketManager_IMX
from core.concurrency import RATE_LIMITERS
import asyncio

router = APIRouter()
router_ws_imx = APIRouter()
ws_manager_imx = WebSocketManager_IMX()

@router.get("/imx477/sensor")
async def get_sensor(request: Request, event: bool = False):
    """Obtiene lectura actual de la cámara IMX477."""
    if not await RATE_LIMITERS["imx477"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones a la cámara IMX477, intente más tarde")
    
    controller = request.app.state.imx_controller
    try:
        data = await asyncio.wait_for(
            controller.get_imx_data(event=event),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data.dict()}
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "La cámara IMX477 no está disponible o no hay datos"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La cámara IMX477 tardó demasiado en responder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer cámara IMX477: {str(e)}")

@router.post("/imx477/sensor")
async def post_sensor(request: Request, payload: SensorIMX477):
    """Guarda una nueva medición de la cámara IMX477."""
    controller = request.app.state.imx_controller
    try:
        result = await controller.create_sensor(payload)
        if result.get("success", True) and "error" not in result.get("msg", "").lower():
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al guardar medición IMX477: {str(e)}"}
        )

@router.put("/imx477/sensor/{sensor_id}")
async def put_sensor(request: Request, sensor_id: int, payload: SensorIMX477):
    """Actualiza una medición existente de la cámara IMX477."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.imx_controller
    try:
        result = await controller.update_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al actualizar medición IMX477: {str(e)}"}
        )

@router.put("/imx477/sensor/{sensor_id}/dual")
async def put_dual_sensor(request: Request, sensor_id: int, payload: SensorIMX477):
    """Completa una medición dual de la cámara IMX477."""
    if sensor_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del sensor debe ser un número positivo")
    
    controller = request.app.state.imx_controller
    try:
        result = await controller.update_dual_sensor(sensor_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al completar medición dual IMX477: {str(e)}"}
        )

@router.delete("/imx477/sensor/project/{project_id}")
async def delete_sensor_by_project(request: Request, project_id: int):
    """Elimina todas las mediciones de IMX477 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    controller = request.app.state.imx_controller
    try:
        result = await controller.delete_sensor(project_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar mediciones IMX477: {str(e)}"}
        )

@router.delete("/imx477/sensor/{record_id}")
async def delete_sensor_by_id(request: Request, record_id: int):
    """Elimina una medición específica de IMX477 por ID."""
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del registro debe ser un número positivo")
    
    controller = request.app.state.imx_controller
    try:
        result = await controller.delete_sensor_by_id(record_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar registro IMX477: {str(e)}"}
        )

@router.get("/imx477/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    """Obtiene las mediciones de IMX477 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["imx477"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.imx_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No se encontraron datos de cámara para el proyecto {project_id}"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La consulta tardó demasiado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar mediciones: {str(e)}")

@router_ws_imx.websocket("/imx477/sensor/ws")
async def imx_ws(websocket: WebSocket):
    await ws_manager_imx.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager_imx.disconnect(websocket)