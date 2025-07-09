#src/schemas/graph_schema.py
from pydantic import BaseModel
from typing import Optional

class GraphCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    sensor_id: str   # el ID viene como string del cliente
    project_id: int

class GraphUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
