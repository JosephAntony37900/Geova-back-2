# TFLuna/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorTFModel(Base):
    __tablename__ = "sensor_tf"

    id_project = Column(Integer, primary_key=True)
    distancia_cm = Column(Integer)
    distancia_m = Column(Float)
    fuerza_senal = Column(Integer)
    temperatura = Column(Float)
    event = Column(Boolean, default=True)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}