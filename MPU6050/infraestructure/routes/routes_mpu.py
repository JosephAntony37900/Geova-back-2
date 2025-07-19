# MPU6050/infraestructure/routes/routes_mpu.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/mpu")
async def get_mpu_data(request: Request, event: bool = False):
    controller = request.app.state.mpu_controller
    data = await controller.get_mpu_data(event=event)
    return data.dict() if data else {"error": "No data"}
