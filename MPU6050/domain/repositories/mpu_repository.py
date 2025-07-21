# MPU6050/domain/repositories/mpu_repository.py
from abc import ABC, abstractmethod
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class MPURepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: SensorMPU, online: bool): pass

    @abstractmethod
    async def exists_by_project(self, project_id: int, online: bool): pass

    @abstractmethod
    async def get_by_project_id(self, project_id: int, online: bool): pass