# TFLuna/infraestructure/repositories/tf_repo_mongo.py
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

    async def exists_by_project(self, project_id: int) -> bool:
        existing = await self.engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
        return existing is not None

    async def get_by_project_id(self, project_id: int) -> SensorTFLuna | None:
        doc = await self.engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
        if doc:
            return SensorTFLuna(**doc.dict())
        return None
