from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Graph(BaseModel):
    title: str
    description: Optional[str] = ""
    sensor_id: str
    project_id: int
    created_at: datetime = datetime.utcnow()
