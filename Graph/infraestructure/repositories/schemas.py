from odmantic import Model, Field
from datetime import datetime

class GraphDocument(Model):
    title: str
    description: str
    sensor_id: str
    project_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
