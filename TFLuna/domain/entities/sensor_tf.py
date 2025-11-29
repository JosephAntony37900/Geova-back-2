from datetime import datetime
from pydantic import BaseModel, field_validator
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
        if v > 1200:  # TF-Luna max range 12m = 1200cm
            raise ValueError('La distancia en cm excede el rango máximo del sensor (1200 cm)')
        return v

    @field_validator('distancia_m')
    @classmethod
    def validate_distancia_m(cls, v):
        if v < 0:
            raise ValueError('La distancia en metros no puede ser negativa')
        if v > 12.0:  # TF-Luna max range 12m
            raise ValueError('La distancia en metros excede el rango máximo del sensor (12 m)')
        return v

    @field_validator('fuerza_senal')
    @classmethod
    def validate_fuerza_senal(cls, v):
        if v < 0:
            raise ValueError('La fuerza de señal no puede ser negativa')
        return v

    @field_validator('temperatura')
    @classmethod
    def validate_temperatura(cls, v):
        if v < -40 or v > 85:
            raise ValueError('La temperatura debe estar entre -40°C y 85°C')
        return v

    @field_validator('measurement_count')
    @classmethod
    def validate_measurement_count(cls, v):
        if v < 1 or v > 2:
            raise ValueError('El measurement_count debe ser 1 o 2')
        return v