# TFLuna/application/tf_usecases.py
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.ports.mqtt_publisher import MQTTPublisher

class TFUseCase:
    def __init__(self, reader, repository: TFLunaRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=True):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorTF(id_project=project_id, event=event, **raw)
        self.publisher.publish(data)

        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorTF):
        if not data.event:
            return {"msg": "No se almacenó porque `event` es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def get_by_project_id(self, project_id: int) -> SensorTF | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)