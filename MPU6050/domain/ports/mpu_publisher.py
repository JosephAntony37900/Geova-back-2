# MPU6050/domain/ports/mpu_publisher.py
from abc import ABC, abstractmethod
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class MPUPublisher(ABC):
    @abstractmethod
    def publish(self, sensor: SensorMPU): pass
