#IMX477/application/sensor_imx.py
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.ports.mqtt_publisher import MQTTPublisher

class IMXUseCase:
    def __init__(self, reader, repository: IMXRepository, publisher: MQTTPublisher):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher

    async def execute(self, project_id=1, resolution="640x480", event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorIMX477(id_project=project_id, resolution=resolution, event=event, **raw)

        self.publisher.publish(data)

        if event:
            await self.repository.save(data)

        return data
