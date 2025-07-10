# --- routes/sensorTF_routes.py ---
from fastapi import APIRouter, Depends
from odmantic import AIOEngine
from src.controllers.sensorTF_controller import read_and_store

router = APIRouter()

@router.get("/sensor")
async def get_sensor_data(engine: AIOEngine = Depends(), event: bool = False):
    data = await read_and_store(engine, event)
    return data.dict() if data else {"error": "No se obtuvo lectura válida"}
