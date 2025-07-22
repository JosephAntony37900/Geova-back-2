from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.ws.ws_manager import WebSocketManager_IMX
from IMX477.infraestructure.ws.ws_imx import VideoStreamer
import asyncio

router = APIRouter()
router_ws_imx = APIRouter()
ws_manager_imx = WebSocketManager_IMX()
streamer = VideoStreamer()

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

@router.get("/imx477/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    controller = request.app.state.imx_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data.dict()
    return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)

@router_ws_imx.websocket("/imx477/sensor/ws")
async def imx_ws(websocket: WebSocket):
    await ws_manager_imx.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_imx.disconnect(websocket)


@router_ws_imx.websocket("/imx477/sensor/ws/live")
async def imx_video_ws(websocket: WebSocket):
    await websocket.accept()
    streamer.register(websocket)

    try:
        while True:
            await asyncio.sleep(1)  # mantener conexión
    except WebSocketDisconnect:
        streamer.unregister(websocket)
