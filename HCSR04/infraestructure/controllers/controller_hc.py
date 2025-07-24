# HCSR04/infraestructure/controllers/hc_controller.py
from HCSR04.application.hc_usecase import HCUseCase
from HCSR04.domain.entities.hc_sensor import HCSensorData

class HCController:
    def __init__(self, usecase: HCUseCase):
        self.usecase = usecase

    async def get_hc_data(self, event: bool = True):
        return await self.usecase.execute(event=event)

    async def create_sensor(self, data: HCSensorData):
        return await self.usecase.create(data)
    
    async def update_sensor(self, project_id: int, data: HCSensorData):
        return await self.usecase.update(project_id, data)
    
    async def delete_sensor(self, project_id: int):
        return await self.usecase.delete(project_id)
    
    async def get_by_project_id(self, project_id: int):
        return await self.usecase.get_by_project_id(project_id)