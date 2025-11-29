# IMX477/domain/entities/sensor_imx.py
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

class SensorIMX477(BaseModel):
    id: int | None = None
    id_project: int
    resolution: str
    luminosidad_promedio: float
    nitidez_score: float
    laser_detectado: bool
    calidad_frame: float
    probabilidad_confiabilidad: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
    is_dual_measurement: bool = False
    measurement_count: int = 1
    avg_luminosidad: Optional[float] = None
    avg_nitidez: Optional[float] = None
    avg_calidad: Optional[float] = None
    avg_probabilidad: Optional[float] = None

    @field_validator('id_project')
    @classmethod
    def validate_id_project(cls, v):
        if v is None or v <= 0:
            raise ValueError('El id_project debe ser un número positivo mayor a 0')
        return v

    @field_validator('resolution')
    @classmethod
    def validate_resolution(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('La resolución no puede estar vacía')
        # Formato esperado: "1920x1080" o similar
        if 'x' not in v.lower():
            raise ValueError('La resolución debe tener formato válido (ej: 1920x1080)')
        return v

    @field_validator('luminosidad_promedio')
    @classmethod
    def validate_luminosidad(cls, v):
        if v < 0 or v > 255:
            raise ValueError('La luminosidad promedio debe estar entre 0 y 255')
        return v

    @field_validator('nitidez_score')
    @classmethod
    def validate_nitidez(cls, v):
        if v < 0:
            raise ValueError('El score de nitidez no puede ser negativo')
        return v

    @field_validator('calidad_frame')
    @classmethod
    def validate_calidad(cls, v):
        if v < 0 or v > 100:
            raise ValueError('La calidad del frame debe estar entre 0 y 100')
        return v

    @field_validator('probabilidad_confiabilidad')
    @classmethod
    def validate_probabilidad(cls, v):
        if v < 0 or v > 100:
            raise ValueError('La probabilidad de confiabilidad debe estar entre 0 y 100')
        return v

    @field_validator('measurement_count')
    @classmethod
    def validate_measurement_count(cls, v):
        if v < 1 or v > 2:
            raise ValueError('El measurement_count debe ser 1 o 2')
        return v