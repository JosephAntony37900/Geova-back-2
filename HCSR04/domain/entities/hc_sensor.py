# HCSR04/domain/entities/hc_sensor.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class HCSensorData(BaseModel):
    id: Optional[int] = None
    id_project: int
    distancia_cm: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
    
    @property
    def distancia_m(self) -> float:
        return self.distancia_cm / 100.0
    
    @property 
    def tiempo_vuelo_us(self) -> float:
        return (self.distancia_cm * 2 * 10) / 3.43  # ida y vuelta