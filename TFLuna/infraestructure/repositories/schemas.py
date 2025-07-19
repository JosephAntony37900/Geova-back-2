#TFLuna/infraestructure/repositories/schemas.py
from odmantic import Model, Field
from typing import Optional
from datetime import datetime

class SensorTFDocument(Model):
    id_project: int 
    distancia_cm: int
    distancia_m: float
    fuerza_senal: int
    temperatura: float
    event: bool = False
    synced: Optional[bool] = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
