from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from IMX477.domain.entities.sensor_imx import SensorIMX477

router = APIRouter()

@router.get("/imx477/sensor")
async def get_sensor(request: Request, event: bool = True):
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
