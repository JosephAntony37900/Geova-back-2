from fastapi import FastAPI
from odmantic import AIOEngine
from Graph.infraestructure.repositories.graph_repo_mongo import GraphRepositoryMongo
from Graph.application.graph_usecase import GraphUseCase
from Graph.infraestructure.controllers.controller_graph import GraphController

def init_graph_dependencies(app: FastAPI, engine: AIOEngine):
    repo = GraphRepositoryMongo(engine)
    usecase = GraphUseCase(repo)
    controller = GraphController(usecase)
    app.state.graph_controller = controller
