#IMX477/infraestructure/controllers/controller_imx.py
from IMX477.application.sensor_imx import IMXUseCase

class IMXController:
    def __init__(self, usecase: IMXUseCase):
        self.usecase = usecase

    async def get_imx_data(self, event=False):
        return await self.usecase.execute(event=event)
