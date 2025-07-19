#TFLuna/domain/repositories/tf_repository.py
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from abc import ABC, abstractmethod

class TFLunaRepository(ABC):
    @abstractmethod
    async def save(self, sensor_data: SensorTF): pass