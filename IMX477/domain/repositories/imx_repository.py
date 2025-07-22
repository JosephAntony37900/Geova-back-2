from abc import ABC, abstractmethod
from IMX477.domain.entities.sensor_imx import SensorIMX477

class IMXRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: SensorIMX477, online: bool): pass

    @abstractmethod
    async def exists_by_project(self, project_id: int, online: bool): pass

    @abstractmethod
    async def get_by_project_id(self, project_id: int, online: bool): pass
