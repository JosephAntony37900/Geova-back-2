#src/models/sensorIMX477_model.py
from odmantic import Model, Field
from datetime import datetime

class SensorIMX477(Model):
    id_project: int
    resolution: str
    luminosidad_promedio: float   # escala 0–255
    nitidez_score: float          # varianza del Laplaciano
    laser_detectado: bool         # si se captó el láser
    calidad_frame: float          # score general de calidad
    probabilidad_confiabilidad: float  # %
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    