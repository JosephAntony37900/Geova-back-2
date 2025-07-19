# MPU6050/domain/repositories/mpu_repository.py
from abc import ABC, abstractmethod
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class MPURepository(ABC):
    @abstractmethod
    async def save(self, data: SensorMPU): pass
