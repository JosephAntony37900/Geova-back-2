from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from HCSR04.domain.entities.hc_sensor import HCSensorData

router = APIRouter()

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
