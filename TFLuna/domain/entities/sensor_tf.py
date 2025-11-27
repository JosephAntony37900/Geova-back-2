from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SensorTFLuna(BaseModel):
    id: int | None = None
    id_project: int
    distancia_cm: int
    distancia_m: float
    fuerza_senal: int
    temperatura: float
    event: bool = True
    timestamp: datetime = datetime.utcnow()
    is_dual_measurement: bool = False
    measurement_count: int = 1
    total_distance_cm: Optional[int] = None
    total_distance_m: Optional[float] = None