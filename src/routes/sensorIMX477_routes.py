from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from src.controllers.sensorIMX477_controller import analizar_frame

router = APIRouter(prefix="/camera", tags=["SensorIMX477"])

@router.get("/analyze")
async def analyze(engine: AIOEngine = Depends(), event: bool = False):
    data = await analizar_frame(engine, event=event)
    return data.dict() if data else {"error": "No se pudo procesar el frame"}
