# MPU6050/domain/entities/sensor_mpu.py
from datetime import datetime
from pydantic import BaseModel

class SensorMPU(BaseModel):
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

