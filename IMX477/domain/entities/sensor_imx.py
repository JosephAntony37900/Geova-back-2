# IMX477/domain/entities/sensor_imx.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SensorIMX477(BaseModel):
    id: int | None = None
    id_project: int
    resolution: str
    luminosidad_promedio: float
    nitidez_score: float
    laser_detectado: bool
    calidad_frame: float
    probabilidad_confiabilidad: float
    event: bool = False
    timestamp: datetime = datetime.utcnow()
    is_dual_measurement: bool = False
    measurement_count: int = 1
    avg_luminosidad: Optional[float] = None
    avg_nitidez: Optional[float] = None
    avg_calidad: Optional[float] = None
    avg_probabilidad: Optional[float] = None