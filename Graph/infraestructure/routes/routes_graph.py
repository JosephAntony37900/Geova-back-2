from fastapi import APIRouter, Request, HTTPException
from Graph.domain.entities.graph import Graph

router = APIRouter(prefix="/graphs", tags=["Graphs"])

@router.post("/")
async def create_graph(data: Graph, request: Request):
    return await request.app.state.graph_controller.create_graph(data)

@router.get("/")
async def list_graphs(request: Request):
    return await request.app.state.graph_controller.list_graphs()

@router.get("/{graph_id}")
async def get_graph(graph_id: str, request: Request):
    graph = await request.app.state.graph_controller.get_graph(graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    return graph

@router.put("/{graph_id}")
async def update_graph(graph_id: str, data: Graph, request: Request):
    updated = await request.app.state.graph_controller.update_graph(graph_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Graph not found")
    return updated

@router.delete("/{graph_id}")
async def delete_graph(graph_id: str, request: Request):
    deleted = await request.app.state.graph_controller.delete_graph(graph_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Graph not found")
    return {"detail": "Graph deleted successfully"}
