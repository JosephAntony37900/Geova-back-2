from odmantic import AIOEngine
from IMX477.infraestructure.repositories.schemas import SensorIMXDocument
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.entities.sensor_imx import SensorIMX477

class IMXRepositoryMongo(IMXRepository):
    def __init__(self, engine: AIOEngine):
        self.engine = engine

    async def save(self, sensor_data: SensorIMX477):
        doc = SensorIMXDocument(**sensor_data.dict())
        await self.engine.save(doc)
