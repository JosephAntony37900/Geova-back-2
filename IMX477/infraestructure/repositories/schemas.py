from odmantic import Model, Field
from datetime import datetime

class SensorIMXDocument(Model):
    id_project: int
    resolution: str
    luminosidad_promedio: float
    nitidez_score: float
    laser_detectado: bool
    calidad_frame: float
    probabilidad_confiabilidad: float
    event: bool = False
    synced: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
