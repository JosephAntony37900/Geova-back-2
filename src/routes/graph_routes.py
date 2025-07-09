from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine
from src.controllers.graph_controller import (
    create_graph, get_all_graphs, get_graph_by_id,
    update_graph, delete_graph
)
from src.schemas.graph_schema import GraphCreate, GraphUpdate

router = APIRouter(prefix="/graphs", tags=["Graphs"])

@router.post("/")
async def create(graph: GraphCreate, engine: AIOEngine = Depends()):
    return await create_graph(engine, graph)

@router.get("/")
async def list_graphs(engine: AIOEngine = Depends()):
    return await get_all_graphs(engine)

@router.get("/{graph_id}")
async def get(graph_id: str, engine: AIOEngine = Depends()):
    graph = await get_graph_by_id(engine, graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Gráfica no encontrada")
    return graph

@router.put("/{graph_id}")
async def update(graph_id: str, update: GraphUpdate, engine: AIOEngine = Depends()):
    updated_graph = await update_graph(engine, graph_id, update)
    if not updated_graph:
        raise HTTPException(status_code=404, detail="No se pudo actualizar la gráfica")
    return updated_graph

@router.delete("/{graph_id}")
async def delete(graph_id: str, engine: AIOEngine = Depends()):
    deleted = await delete_graph(engine, graph_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No se pudo eliminar la gráfica")
    return {"detail": "Gráfica eliminada correctamente"}
