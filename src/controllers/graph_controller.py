#src/controllers/graph_controller.py
from odmantic import AIOEngine, ObjectId
from src.models.graph_model import Graph
from src.schemas.graph_schema import GraphCreate, GraphUpdate

async def create_graph(engine: AIOEngine, data: GraphCreate):
    graph = Graph(
        title=data.title,
        description=data.description,
        sensor_id=ObjectId(data.sensor_id),
        project_id=data.project_id
    )
    await engine.save(graph)
    return graph

async def get_all_graphs(engine: AIOEngine):
    return await engine.find(Graph)

async def get_graph_by_id(engine: AIOEngine, graph_id: str):
    return await engine.find_one(Graph, Graph.id == ObjectId(graph_id))

async def update_graph(engine: AIOEngine, graph_id: str, update_data: GraphUpdate):
    graph = await get_graph_by_id(engine, graph_id)
    if not graph:
        return None
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(graph, field, value)
    await engine.save(graph)
    return graph

async def delete_graph(engine: AIOEngine, graph_id: str):
    graph = await get_graph_by_id(engine, graph_id)
    if not graph:
        return False
    await engine.delete(graph)
    return True
