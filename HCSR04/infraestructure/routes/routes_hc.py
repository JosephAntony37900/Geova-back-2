# HCSR04/infraestructure/routes/routes_hc.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/hc-sensor")
async def get_hc_sensor(request: Request, event: bool = True):
    controller = request.app.state.hc_controller
    data = await controller.get_hc_data(event=event)
    return data.dict() if data else {"error": "No data"}
