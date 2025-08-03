# IMX477/domain/repositories/imx_repository.py
from abc import ABC, abstractmethod
from IMX477.domain.entities.sensor_imx import SensorIMX477

class IMXRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: SensorIMX477, online: bool): pass

    @abstractmethod
    async def update(self, sensor_data: SensorIMX477, online: bool): pass

    @abstractmethod
    async def delete(self, project_id: int, online: bool): pass

    @abstractmethod
    async def delete_by_id(self, record_id: int, online: bool): pass

    @abstractmethod
    async def exists_by_project(self, project_id: int, online: bool): pass

    @abstractmethod
    async def get_by_project_id(self, project_id: int, online: bool): pass
    
    @abstractmethod
    async def get_dual_measurement(self, project_id: int, online: bool): pass

    @abstractmethod
    async def exists_dual_measurement(self, project_id: int, online: bool): pass
    
    @abstractmethod
    async def has_any_record(self, project_id: int, online: bool): pass
    
    @abstractmethod
    async def get_by_id(self, record_id: int, online: bool): pass