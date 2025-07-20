# HCSR04/domain/entities/hc_sensor.py
from pydantic import BaseModel, Field
from datetime import datetime

class HCSensorData(BaseModel):
    id_project: int
    distancia_cm: float
    event: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
