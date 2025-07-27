# MPU6050/infraestructure/repositories/schemas_sqlalchemy.py
from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorMPUModel(Base):
    __tablename__ = "sensor_mpu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_project = Column(Integer, index=True)
    ax = Column(Float)
    ay = Column(Float)
    az = Column(Float)
    gx = Column(Float)
    gy = Column(Float)
    gz = Column(Float)
    roll = Column(Float)
    pitch = Column(Float)
    apertura = Column(Float)
    event = Column(Boolean, default=False)
    synced = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}