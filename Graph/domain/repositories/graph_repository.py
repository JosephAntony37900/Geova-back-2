from abc import ABC, abstractmethod
from Graph.domain.entities.graph import Graph

class GraphRepository(ABC):
    @abstractmethod
    async def save(self, graph: Graph): pass

    @abstractmethod
    async def get_all(self): pass

    @abstractmethod
    async def get_by_id(self, graph_id: str): pass

    @abstractmethod
    async def update(self, graph_id: str, graph: Graph): pass

    @abstractmethod
    async def delete(self, graph_id: str): pass
