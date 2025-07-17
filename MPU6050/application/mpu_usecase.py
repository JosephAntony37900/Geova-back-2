# MPU6050/application/mpu_usecase.py
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.ports.mpu_publisher import MPUPublisher

class MPUUseCase:
    def __init__(self, reader, repository: MPURepository, publisher: MPUPublisher):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorMPU(id_project=project_id, event=event, **raw)
        self.publisher.publish(data)

        if event:
            await self.repository.save(data)

        return data
