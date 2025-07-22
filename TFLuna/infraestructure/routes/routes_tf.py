# TFLuna/infraestructure/routes/routes_tf.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.infraestructure.ws.ws_manager import WebSocketManager

router_ws_tf = APIRouter()
ws_manager = WebSocketManager()
router = APIRouter()

@router.get("/tfluna/sensor")
async def get_sensor(request: Request, event: bool = False):
    controller = request.app.state.tf_controller
    data = await controller.get_tf_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router.post("/tfluna/sensor")
async def post_sensor(request: Request, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.get("/tfluna/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    controller = request.app.state.tf_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data.dict()
    return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)

@router_ws_tf.websocket("/tfluna/sensor/ws")
async def tf_luna_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantener la conexión viva
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
