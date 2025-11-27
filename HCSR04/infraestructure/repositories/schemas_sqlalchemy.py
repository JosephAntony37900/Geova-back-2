# HCSR04/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorHCModel(Base):
    __tablename__ = "sensor_hc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_project = Column(Integer, nullable=False, index=True)
    distancia_cm = Column(Float, nullable=False)
    distancia_m = Column(Float, nullable=False)
    tiempo_vuelo_us = Column(Float, nullable=False)
    event = Column(Boolean, default=True)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_project_timestamp', 'id_project', 'timestamp'),
    )

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}