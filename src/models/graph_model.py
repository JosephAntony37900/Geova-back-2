#src/models/graph_model.py
from odmantic import Model, ObjectId
from datetime import datetime

class Graph(Model):
    title: str
    description: str
    sensor_id: ObjectId  # Relación al sensor
    project_id: int      # Id del proyecto asociado
    created_at: datetime = datetime.utcnow()
