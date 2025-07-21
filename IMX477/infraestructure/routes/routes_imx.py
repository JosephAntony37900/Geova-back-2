#IMX477/infraestructure/routes/routes_imx.py
from fastapi import APIRouter, Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from IMX477.infraestructure.ws.ws_manager import WebSocketManager_IMX
from IMX477.infraestructure.ws.ws_imx import VideoStreamer
from fastapi import WebSocket, WebSocketDisconnect
router = APIRouter(prefix="/camera", tags=["IMX477"])

router_ws_imx = APIRouter()
ws_manager_imx = WebSocketManager_IMX()
streamer = VideoStreamer()

@router.get("/analyze")
async def analyze(req: Request, event: bool = False):
    data = await req.app.state.imx_controller.get_imx_data(event=event)
    return data.dict() if data else {"error": "No se pudo procesar el frame"}

@router_ws_imx.websocket("/ws/imx")
async def imx_ws(websocket: WebSocket):
    await ws_manager_imx.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_imx.disconnect(websocket)


@router_ws_imx.websocket("/ws/imx/live")
async def imx_video_ws(websocket: WebSocket):
    await websocket.accept()
    streamer.register(websocket)

    try:
        while True:
            await asyncio.sleep(1)  # mantener conexión
    except WebSocketDisconnect:
        streamer.unregister(websocket)
