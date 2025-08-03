# IMX477/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorIMX477Model(Base):
    __tablename__ = "sensor_imx"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_project = Column(Integer, index=True)
    resolution = Column(String)
    luminosidad_promedio = Column(Float)
    nitidez_score = Column(Float)
    laser_detectado = Column(Boolean)
    calidad_frame = Column(Float)
    probabilidad_confiabilidad = Column(Float)
    event = Column(Boolean, default=False)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_dual_measurement = Column(Boolean, default=False)
    measurement_count = Column(Integer, default=1)
    avg_luminosidad = Column(Float, nullable=True)
    avg_nitidez = Column(Float, nullable=True)
    avg_calidad = Column(Float, nullable=True)
    avg_probabilidad = Column(Float, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}