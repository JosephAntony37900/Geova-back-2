# MPU6050/infraestructure/controllers/controller_mpu.py
from MPU6050.application.mpu_usecase import MPUUseCase

class MPUController:
    def __init__(self, usecase: MPUUseCase):
        self.usecase = usecase

    async def get_mpu_data(self, event: bool = False):
        return await self.usecase.execute(event=event)
