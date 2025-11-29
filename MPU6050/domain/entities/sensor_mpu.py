# MPU6050/domain/entities/sensor_mpu.py
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

class SensorMPU(BaseModel):
    id: int | None = None
    id_project: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float
    roll: float
    pitch: float
    apertura: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
    is_dual_measurement: bool = False
    measurement_count: int = 1

    @field_validator('id_project')
    @classmethod
    def validate_id_project(cls, v):
        if v is None or v <= 0:
            raise ValueError('El id_project debe ser un número positivo mayor a 0')
        return v

    @field_validator('ax', 'ay', 'az')
    @classmethod
    def validate_aceleracion(cls, v):
        # MPU6050 rango típico: ±2g, ±4g, ±8g, ±16g
        if v < -20 or v > 20:
            raise ValueError('Los valores de aceleración deben estar entre -20 y 20 g')
        return v

    @field_validator('gx', 'gy', 'gz')
    @classmethod
    def validate_giroscopio(cls, v):
        # MPU6050 rango típico: ±250, ±500, ±1000, ±2000 °/s
        if v < -2500 or v > 2500:
            raise ValueError('Los valores del giroscopio deben estar entre -2500 y 2500 °/s')
        return v

    @field_validator('roll', 'pitch')
    @classmethod
    def validate_angulos(cls, v):
        if v < -180 or v > 180:
            raise ValueError('Los ángulos roll/pitch deben estar entre -180° y 180°')
        return v

    @field_validator('apertura')
    @classmethod
    def validate_apertura(cls, v):
        if v < 0 or v > 180:
            raise ValueError('La apertura debe estar entre 0° y 180°')
        return v

    @field_validator('measurement_count')
    @classmethod
    def validate_measurement_count(cls, v):
        if v < 1 or v > 2:
            raise ValueError('El measurement_count debe ser 1 o 2')
        return v