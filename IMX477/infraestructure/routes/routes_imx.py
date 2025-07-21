from fastapi import APIRouter, Request
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from IMX477.infraestructure.ws.ws_manager import WebSocketManager_IMX
router = APIRouter(prefix="/camera", tags=["IMX477"])

router_ws_imx = APIRouter()
ws_manager_imx = WebSocketManager_IMX()


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