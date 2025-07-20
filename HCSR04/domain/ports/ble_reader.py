# HCSR04/domain/ports/ble_reader.py
from abc import ABC, abstractmethod

class BLEReader(ABC):
    @abstractmethod
    def read(self) -> dict:
        pass
