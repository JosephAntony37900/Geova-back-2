from IMX477.application.sensor_imx import IMXUseCase
from IMX477.domain.entities.sensor_imx import SensorIMX477

class IMXController:
    def __init__(self, usecase: IMXUseCase):
        self.usecase = usecase

    async def get_imx_data(self, event: bool = True):
        return await self.usecase.execute(event=event)

    async def create_sensor(self, data: SensorIMX477):
        return await self.usecase.create(data)
    
    async def get_by_project_id(self, project_id: int):
        return await self.usecase.get_by_project_id(project_id)
