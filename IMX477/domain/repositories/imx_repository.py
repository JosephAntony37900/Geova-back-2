from abc import ABC, abstractmethod
from IMX477.domain.entities.sensor_imx import SensorIMX477

class IMXRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: SensorIMX477): pass
