# HCSR04/domain/repositories/hc_repository.py
from abc import ABC, abstractmethod
from HCSR04.domain.entities.hc_sensor import HCSensorData

class HCSensorRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: HCSensorData, online: bool): pass

    @abstractmethod
    async def update(self, sensor_data: HCSensorData, online: bool): pass

    @abstractmethod
    async def delete(self, project_id: int, online: bool): pass

    @abstractmethod
    async def exists_by_project(self, project_id: int, online: bool): pass

    @abstractmethod
    async def get_by_project_id(self, project_id: int, online: bool): pass