# --- src/models/sensorTF_model.py ---
from odmantic import Model, Field
from datetime import datetime

class SensorTF(Model):
    id_project: int 
    distancia_cm: int
    distancia_m: float
    fuerza_senal: int
    temperatura: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)