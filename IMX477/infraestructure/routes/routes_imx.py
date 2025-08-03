# IMX477/infraestructure/routes/routes_imx.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.ws.ws_manager import WebSocketManager_IMX

router = APIRouter()
router_ws_imx = APIRouter()
ws_manager_imx = WebSocketManager_IMX()

@router.get("/imx477/sensor")
async def get_sensor(request: Request, event: bool = False):
    controller = request.app.state.imx_controller
    data = await controller.get_imx_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router.post("/imx477/sensor")
async def post_sensor(request: Request, payload: SensorIMX477):
    controller = request.app.state.imx_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.put("/imx477/sensor/{sensor_id}")
async def put_sensor(request: Request, sensor_id: int, payload: SensorIMX477):
    controller = request.app.state.imx_controller
    result = await controller.update_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.put("/imx477/sensor/{sensor_id}/dual")
async def put_dual_sensor(request: Request, sensor_id: int, payload: SensorIMX477):
    controller = request.app.state.imx_controller
    result = await controller.update_dual_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=400)

@router.delete("/imx477/sensor/project/{project_id}")
async def delete_sensor_by_project(request: Request, project_id: int):
    controller = request.app.state.imx_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/imx477/sensor/{record_id}")
async def delete_sensor_by_id(request: Request, record_id: int):
    controller = request.app.state.imx_controller
    result = await controller.delete_sensor_by_id(record_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/imx477/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    controller = request.app.state.imx_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data
    return JSONResponse(content={"error": "No se encontró datos de la cámara para ese proyecto"}, status_code=404)

@router_ws_imx.websocket("/imx477/sensor/ws")
async def imx_ws(websocket: WebSocket):
    await ws_manager_imx.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager_imx.disconnect(websocket)