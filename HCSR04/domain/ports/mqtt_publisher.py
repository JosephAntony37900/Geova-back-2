# HCSR04/domain/ports/mqtt_publisher.py
from abc import ABC, abstractmethod
from HCSR04.domain.entities.hc_sensor import HCSensorData

class MQTTPublisher(ABC):
    @abstractmethod
    def publish(self, sensor: HCSensorData): pass
