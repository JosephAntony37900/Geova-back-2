# TFLuna/infraestructure/controllers/controller_tf.py
from TFLuna.application.tf_usecases import TFUseCase
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF

class TFController:
    def __init__(self, usecase: TFUseCase):
        self.usecase = usecase

    async def get_tf_data(self, event: bool = False):
        return await self.usecase.execute(event=event)

    async def create_sensor(self, data: SensorTF):
        return await self.usecase.create(data)
    
    async def get_by_project_id(self, project_id: int):
        return await self.usecase.get_by_project_id(project_id)

