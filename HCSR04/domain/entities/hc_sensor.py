# HCSR04/domain/entities/hc_sensor.py
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

class HCSensorData(BaseModel):
    id: Optional[int] = None
    id_project: int
    distancia_cm: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()

    @field_validator('id_project')
    @classmethod
    def validate_id_project(cls, v):
        if v is None or v <= 0:
            raise ValueError('El id_project debe ser un número positivo mayor a 0')
        return v

    @field_validator('distancia_cm')
    @classmethod
    def validate_distancia_cm(cls, v):
        if v < 0:
            raise ValueError('La distancia en cm no puede ser negativa')
        if v > 400:  # HC-SR04 max range ~4m = 400cm
            raise ValueError('La distancia en cm excede el rango máximo del sensor (400 cm)')
        return v
    
    @property
    def distancia_m(self) -> float:
        return self.distancia_cm / 100.0
    
    @property 
    def tiempo_vuelo_us(self) -> float:
        return (self.distancia_cm * 2 * 10) / 3.43  # ida y vuelta