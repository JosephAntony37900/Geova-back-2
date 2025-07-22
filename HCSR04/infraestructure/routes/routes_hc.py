from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.infraestructure.ws.ws_manager import WebSocketManager_HC

router = APIRouter()
router_ws_hc = APIRouter()
ws_manager_hc = WebSocketManager_HC()

@router.get("/hc/sensor")
async def get_hc_sensor(request: Request, event: bool = True):
    controller = request.app.state.hc_controller
    data = await controller.get_hc_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router.post("/hc/sensor")
async def post_hc_sensor(request: Request, payload: HCSensorData):
    controller = request.app.state.hc_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.get("/hc/sensor/{project_id}")
async def get_hc_sensor_by_project_id(request: Request, project_id: int):
    controller = request.app.state.hc_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data.dict()
    return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)

@router_ws_hc.websocket("/hc/sensor/ws")
async def hc_ws(websocket: WebSocket):
    await ws_manager_hc.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager_hc.disconnect(websocket)