# HCSR04/infraestructure/repositories/hc_repo_mongo.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.infraestructure.repositories.schemas import SensorHCSR04
class MongoHCSensorRepository(HCSensorRepository):
    def __init__(self, engine):
        self.engine = engine

    async def save(self, sensor_data: HCSensorData):
        doc = SensorHCSR04(**sensor_data.dict())
        await self.engine.save(doc)

