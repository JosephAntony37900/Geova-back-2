# TFLuna/infraestructure/routes/routes_tf.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/sensor")
async def get_sensor(request: Request, event: bool = True):
    controller = request.app.state.tf_controller
    data = await controller.get_tf_data(event=event)
    return data.dict() if data else {"error": "No data"}
