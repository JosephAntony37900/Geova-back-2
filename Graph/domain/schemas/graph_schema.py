from pydantic import BaseModel
from typing import Optional

class GraphCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    sensor_id: str
    project_id: int

class GraphUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
