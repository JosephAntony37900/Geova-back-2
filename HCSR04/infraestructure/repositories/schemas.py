# HCSR04/infraestructure/repositories/schemas.py
from odmantic import Model, Field
from datetime import datetime

class SensorHCSR04(Model):
    id_project: int
    distancia_cm: float
    event: bool = True
    synced: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
