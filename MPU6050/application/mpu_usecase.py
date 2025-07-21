# MPU6050/application/mpu_usecase.py
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.ports.mpu_publisher import MPUPublisher

class MPUUseCase:
    def __init__(self, reader, repository: MPURepository, publisher: MPUPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorMPU(id_project=project_id, event=event, **raw)
        self.publisher.publish(data)

        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorMPU):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición con el sensor de inclinación MPU6050 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def get_by_project_id(self, project_id: int) -> SensorMPU | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)