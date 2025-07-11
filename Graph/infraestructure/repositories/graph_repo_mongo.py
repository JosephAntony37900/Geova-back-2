from odmantic import AIOEngine, ObjectId
from Graph.domain.repositories.graph_repository import GraphRepository
from Graph.domain.entities.graph import Graph
from Graph.infraestructure.repositories.schemas import GraphDocument

class GraphRepositoryMongo(GraphRepository):
    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def save(self, graph: Graph):
        doc = GraphDocument(**graph.dict())
        await self.engine.save(doc)
        return doc

    async def get_all(self):
        return await self.engine.find(GraphDocument)

    async def get_by_id(self, graph_id: str):
        return await self.engine.find_one(GraphDocument, GraphDocument.id == ObjectId(graph_id))

    async def update(self, graph_id: str, graph: Graph):
        doc = await self.get_by_id(graph_id)
        if not doc:
            return None
        for key, value in graph.dict(exclude_unset=True).items():
            setattr(doc, key, value)
        await self.engine.save(doc)
        return doc

    async def delete(self, graph_id: str):
        doc = await self.get_by_id(graph_id)
        if not doc:
            return False
        await self.engine.delete(doc)
        return True
