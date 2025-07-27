#TFLuna/domain/entities/sensor_tf.py
from datetime import datetime
from pydantic import BaseModel

class SensorTFLuna(BaseModel):
    id: int | None = None
    id_project: int
    distancia_cm: int
    distancia_m: float
    fuerza_senal: int
    temperatura: float
    event: bool = True
    timestamp: datetime = datetime.utcnow()
