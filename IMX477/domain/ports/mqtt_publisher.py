from abc import ABC, abstractmethod
from IMX477.domain.entities.sensor_imx import SensorIMX477

class MQTTPublisher(ABC):
    @abstractmethod
    def publish(self, sensor: SensorIMX477): pass
