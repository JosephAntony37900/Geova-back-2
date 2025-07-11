from Graph.domain.entities.graph import Graph
from Graph.domain.repositories.graph_repository import GraphRepository

class GraphUseCase:
    def __init__(self, repository: GraphRepository):
        self.repository = repository

    async def create(self, data: Graph):
        return await self.repository.save(data)

    async def list_all(self):
        return await self.repository.get_all()

    async def get_by_id(self, graph_id: str):
        return await self.repository.get_by_id(graph_id)

    async def update(self, graph_id: str, data: Graph):
        return await self.repository.update(graph_id, data)

    async def delete(self, graph_id: str):
        return await self.repository.delete(graph_id)
