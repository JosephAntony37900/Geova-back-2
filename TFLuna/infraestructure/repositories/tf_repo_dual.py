#TFLuna/infraestructure/repositories/tf_repo_dual.py
from odmantic import AIOEngine
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.infraestructure.repositories.schemas import SensorTF as SensorTFModel

class TFLunaDualRepository(TFLunaRepository):
    def __init__(self, local_engine: AIOEngine, remote_engine: AIOEngine):
        self.local_engine = local_engine
        self.remote_engine = remote_engine
        print("remote engine", remote_engine)
        print("local engine", local_engine)

    async def save(self, sensor_data: SensorTFLuna, online: bool):
        model = SensorTFModel(**sensor_data.dict(), synced=False)
        await self.local_engine.save(model)

        if online:
            try:
                await self.remote_engine.save(model)
                model.synced = True
                await self.local_engine.save(model)
                print("✅ Guardado en remoto")
            except Exception as e:
                print(f"❌ Error al guardar en remoto: {e}")
        else:
            print("📡 Sin internet, solo local")

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        if online:
            try:
                doc = await self.remote_engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
                return doc is not None
            except:
                pass
        doc = await self.local_engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
        return doc is not None

    async def get_by_project_id(self, project_id: int, online: bool) -> SensorTFLuna | None:
        if online:
            try:
                doc = await self.remote_engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
                if doc:
                    return SensorTFLuna(**doc.dict())
            except:
                pass
        doc = await self.local_engine.find_one(SensorTFModel, SensorTFModel.id_project == project_id)
        if doc:
            return SensorTFLuna(**doc.dict())
        return None
