from odmantic import AIOEngine
from TFLuna.infraestructure.repositories.schemas import SensorTF as SensorTFModel
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.domain.repositories.tf_repository import TFLunaRepository

class TFLunaRepositoryMongo(TFLunaRepository):
    def __init__(self, engine: AIOEngine):
        self.engine = engine
        
    async def save(self, sensor_data: SensorTFLuna):
        document = SensorTFModel(**sensor_data.dict(), synced=False)
        await self.engine.save(document)
