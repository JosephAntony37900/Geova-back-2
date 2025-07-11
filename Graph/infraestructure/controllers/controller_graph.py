from Graph.application.graph_usecase import GraphUseCase
from Graph.domain.entities.graph import Graph

class GraphController:
    def __init__(self, usecase: GraphUseCase):
        self.usecase = usecase

    async def create_graph(self, data: Graph):
        return await self.usecase.create(data)

    async def list_graphs(self):
        return await self.usecase.list_all()

    async def get_graph(self, graph_id: str):
        return await self.usecase.get_by_id(graph_id)

    async def update_graph(self, graph_id: str, data: Graph):
        return await self.usecase.update(graph_id, data)

    async def delete_graph(self, graph_id: str):
        return await self.usecase.delete(graph_id)
