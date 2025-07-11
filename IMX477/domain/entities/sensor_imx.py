from datetime import datetime
from pydantic import BaseModel

class SensorIMX477(BaseModel):
    id_project: int
    resolution: str
    luminosidad_promedio: float
    nitidez_score: float
    laser_detectado: bool
    calidad_frame: float
    probabilidad_confiabilidad: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
