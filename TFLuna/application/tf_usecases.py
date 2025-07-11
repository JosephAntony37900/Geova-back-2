#TFLuna/application/tf_usecase.py
from TFLuna.domain.entities.sensor_tf import SensorTF
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.ports.mqtt_publisher import MQTTPublisher

class TFUseCase:
    def __init__(self, reader, repository: TFLunaRepository, publisher: MQTTPublisher):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorTF(id_project=project_id, event=event, **raw)

        # Publicar SIEMPRE por el puerto (sin saber que es Rabbit)
        self.publisher.publish(data)

        if event:
            await self.repository.save(data)

        return data
