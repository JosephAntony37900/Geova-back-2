# MPU6050/infraestructure/repositories/mpu_repo_mongo.py
from odmantic import AIOEngine
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.infraestructure.repositories.schemas import SensorMPUDocument

class MPURepositoryMongo(MPURepository):
    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def save(self, data: SensorMPU):
        document = SensorMPUDocument(**data.dict(), synced=False)
        await self.engine.save(document)
