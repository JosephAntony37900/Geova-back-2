# MPU6050/infraestructure/repositories/schemas.py
from odmantic import Model, Field
from datetime import datetime

class SensorMPUDocument(Model):
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
    synced: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
