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
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["hcsr04"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.hc_controller
    try:
        data = await asyncio.wait_for(
            controller.get_hc_data(project_id=project_id, event=event),
            timeout=5.0
        )
        return data.dict() if data else {"error": "No data available"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout obteniendo datos del sensor")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hc/sensor")
async def post_hc_sensor(request: Request, payload: HCSensorData):
    controller = request.app.state.hc_controller
    result = await controller.create_sensor(payload)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=400)

@router.put("/hc/sensor/{project_id}")
async def put_hc_sensor(request: Request, project_id: int, payload: HCSensorData):
    controller = request.app.state.hc_controller
    result = await controller.update_sensor(project_id, payload)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/hc/sensor/{project_id}")
async def delete_hc_sensor(request: Request, project_id: int):
    controller = request.app.state.hc_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/hc/sensor/{project_id}")
async def get_hc_sensor_by_project_id(request: Request, project_id: int):
    # Rate limiting para evitar saturación
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
                "project_id": project_id,
                "total_measurements": len(data),
                "measurements": [measurement.dict() for measurement in data]
            }
        return JSONResponse(
            content={"error": "No se encontraron mediciones para ese proyecto"}, 
            status_code=404
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout consultando base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hc/sensor/{project_id}/latest")
async def get_hc_sensor_latest_by_project_id(request: Request, project_id: int):
    # Rate limiting para evitar saturación
    if not await RATE_LIMITERS["hcsr04"].acquire():
        raise HTTPException(status_code=429, detail="Demasiadas peticiones, intente más tarde")
    
    controller = request.app.state.hc_controller
    try:
        data = await asyncio.wait_for(
            controller.get_latest_by_project_id(project_id),
            timeout=5.0
        )
        
        if data:
            return data.dict()
        return JSONResponse(
            content={"error": "No se encontró ninguna medición para ese proyecto"}, 
            status_code=404
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout consultando base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_ws_hc.websocket("/hc/sensor/ws")
async def hc_ws(websocket: WebSocket):
    await ws_manager_hc.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_hc.disconnect(websocket)