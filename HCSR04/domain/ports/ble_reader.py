# HCSR04/domain/ports/ble_reader.py
from abc import ABC, abstractmethod

class BLEReader(ABC):
    @abstractmethod
    def read(self) -> dict | None:
        pass
    
    @abstractmethod
    async def read_async(self) -> dict | None:
        pass