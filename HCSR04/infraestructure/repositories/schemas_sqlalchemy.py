# HCSR04/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorHCModel(Base):
    __tablename__ = "sensor_hc"

    id_project = Column(Integer, primary_key=True)
    distancia_cm = Column(Float)
    event = Column(Boolean, default=True)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}