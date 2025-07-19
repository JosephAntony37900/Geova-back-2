#TFLuna/domain/ports/mqtt_publisher.py
from abc import ABC, abstractmethod
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF

class MQTTPublisher(ABC):
    @abstractmethod
    def publish(self, sensor: SensorTF): pass
