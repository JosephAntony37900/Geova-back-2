# MPU6050/infraestructure/controllers/controller_mpu.py
from MPU6050.application.mpu_usecase import MPUUseCase
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class MPUController:
    def __init__(self, usecase: MPUUseCase):
        self.usecase = usecase

    async def get_mpu_data(self, event: bool = False):
        return await self.usecase.execute(event=event)

    async def create_sensor(self, data: SensorMPU):
        return await self.usecase.create(data)
    
    async def get_by_project_id(self, project_id: int):
        return await self.usecase.get_by_project_id(project_id)