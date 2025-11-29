# HCSR04/infraestructure/routes/routes_hc.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.infraestructure.ws.ws_manager import WebSocketManager_HC
from typing import List
from core.concurrency import RATE_LIMITERS
import asyncio

router = APIRouter()
router_ws_hc = APIRouter()
ws_manager_hc = WebSocketManager_HC()

@router.get("/hc/sensor")
async def get_hc_sensor(request: Request, project_id: int = Query(1), event: bool = True):
    """Obtiene lectura actual del sensor HC-SR04 (ultrasonido)."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["hcsr04"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones al sensor HC-SR04, intente más tarde")
    
    controller = request.app.state.hc_controller
    try:
        data = await asyncio.wait_for(
            controller.get_hc_data(project_id=project_id, event=event),
            timeout=5.0
        )
        if data:
            return {"success": True, "data": data.dict()}
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "El sensor HC-SR04 no está disponible o no hay datos"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: El sensor HC-SR04 tardó demasiado en responder")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer sensor HC-SR04: {str(e)}")

@router.post("/hc/sensor")
async def post_hc_sensor(request: Request, payload: HCSensorData):
    """Guarda una nueva medición del sensor HC-SR04."""
    controller = request.app.state.hc_controller
    try:
        result = await controller.create_sensor(payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=400)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al guardar medición HC-SR04: {str(e)}"}
        )

@router.put("/hc/sensor/{project_id}")
async def put_hc_sensor(request: Request, project_id: int, payload: HCSensorData):
    """Actualiza las mediciones del sensor HC-SR04 para un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    controller = request.app.state.hc_controller
    try:
        result = await controller.update_sensor(project_id, payload)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al actualizar medición HC-SR04: {str(e)}"}
        )

@router.delete("/hc/sensor/{project_id}")
async def delete_hc_sensor(request: Request, project_id: int):
    """Elimina todas las mediciones de HC-SR04 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    controller = request.app.state.hc_controller
    try:
        result = await controller.delete_sensor(project_id)
        if result.get("success", True):
            return JSONResponse(content={"success": True, **result})
        return JSONResponse(content={"success": False, **result}, status_code=404)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Error al eliminar mediciones HC-SR04: {str(e)}"}
        )

@router.get("/hc/sensor/{project_id}")
async def get_hc_sensor_by_project_id(request: Request, project_id: int):
    """Obtiene las mediciones de HC-SR04 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["hcsr04"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.hc_controller
    try:
        data = await asyncio.wait_for(
            controller.get_by_project_id(project_id),
            timeout=5.0
        )
        
        if data:
            return {
                "success": True,
                "project_id": project_id,
                "total_measurements": len(data),
                "measurements": [measurement.dict() for measurement in data]
            }
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No se encontraron mediciones HC-SR04 para el proyecto {project_id}"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La consulta tardó demasiado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar mediciones: {str(e)}")

@router.get("/hc/sensor/{project_id}/latest")
async def get_hc_sensor_latest_by_project_id(request: Request, project_id: int):
    """Obtiene la última medición de HC-SR04 de un proyecto."""
    if project_id <= 0:
        raise HTTPException(status_code=400, detail="El ID del proyecto debe ser un número positivo")
    
    if not await RATE_LIMITERS["hcsr04"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.hc_controller
    try:
        data = await asyncio.wait_for(
            controller.get_latest_by_project_id(project_id),
            timeout=5.0
        )
        
        if data:
            return {"success": True, "data": data.dict()}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"No se encontró ninguna medición HC-SR04 para el proyecto {project_id}"}
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout: La consulta tardó demasiado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar medición: {str(e)}")

@router_ws_hc.websocket("/hc/sensor/ws")
async def hc_ws(websocket: WebSocket):
    await ws_manager_hc.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_hc.disconnect(websocket)