# HCSR04/infraestructure/repositories/hc_repo_mongo.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.infraestructure.repositories.schemas import HCSensorDoc

class MongoHCSensorRepository(HCSensorRepository):
    async def save(self, sensor_data: HCSensorData, engine):
        doc = HCSensorDoc(**sensor_data.dict())
        await engine.save(doc)
