#TFLuna/domain/entities/sensor_tf.py
from datetime import datetime
from pydantic import BaseModel

class SensorTF(BaseModel):
    id_project: int
    distancia_cm: int
    distancia_m: float
    fuerza_senal: int
    temperatura: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
