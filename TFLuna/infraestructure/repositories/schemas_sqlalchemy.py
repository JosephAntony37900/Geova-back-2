# TFLuna/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorTFModel(Base):
    __tablename__ = "sensor_tf"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_project = Column(Integer, index=True)
    distancia_cm = Column(Integer)
    distancia_m = Column(Float)
    fuerza_senal = Column(Integer)
    temperatura = Column(Float)
    event = Column(Boolean, default=False)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_dual_measurement = Column(Boolean, default=False, nullable=False)
    measurement_count = Column(Integer, default=1, nullable=False)
    total_distance_cm = Column(Integer, nullable=True)
    total_distance_m = Column(Float, nullable=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}