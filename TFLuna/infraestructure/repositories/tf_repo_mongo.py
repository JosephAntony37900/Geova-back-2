#TFLuna/infraestructure/repositories/tf_repo_mongo.py
from odmantic import AIOEngine
from TFLuna.infraestructure.repositories.schemas import SensorTFDocument
from TFLuna.domain.entities.sensor_tf import SensorTF
from TFLuna.domain.repositories.tf_repository import TFLunaRepository

class TFLunaRepositoryMongo(TFLunaRepository):
    def __init__(self, engine: AIOEngine):
        self.engine = engine
        
    async def save(self, sensor_data: SensorTF):
        document = SensorTFDocument(**sensor_data.dict())
        await self.engine.save(document)