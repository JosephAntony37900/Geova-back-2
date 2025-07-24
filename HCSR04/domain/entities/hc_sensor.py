#HCSR04/domain/entities/hc_sensor.py
from datetime import datetime
from pydantic import BaseModel

class HCSensorData(BaseModel):
    id_project: int
    distancia_cm: float
    event: bool = True
    timestamp: datetime = datetime.utcnow()