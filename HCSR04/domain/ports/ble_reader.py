from abc import ABC, abstractmethod

class BLEReader(ABC):
    @abstractmethod
    def read(self) -> dict:
        pass