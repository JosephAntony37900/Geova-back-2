# HCSR04/domain/repositories/hc_repository.py
from abc import ABC, abstractmethod
from HCSR04.domain.entities.hc_sensor import HCSensorData

class HCSensorRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: HCSensorData, engine): pass
