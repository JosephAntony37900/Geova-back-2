# HCSR04/domain/repositories/hc_repository.py
from abc import ABC, abstractmethod
from HCSR04.domain.entities.hc_sensor import HCSensorData
from typing import List

class HCSensorRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: HCSensorData, online: bool): 
        pass

    @abstractmethod
    async def update_all_by_project(self, project_id: int, sensor_data: HCSensorData, online: bool): 
        pass

    @abstractmethod
    async def delete_all_by_project(self, project_id: int, online: bool): 
        pass

    @abstractmethod
    async def exists_by_project(self, project_id: int, online: bool) -> bool: 
        pass

    @abstractmethod
    async def get_all_by_project_id(self, project_id: int, online: bool) -> List[HCSensorData]: 
        pass

    @abstractmethod
    async def get_latest_by_project_id(self, project_id: int, online: bool) -> HCSensorData | None: 
        pass