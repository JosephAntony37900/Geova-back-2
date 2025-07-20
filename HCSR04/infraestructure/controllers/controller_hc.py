# HCSR04/infraestructure/controllers/controller_hc.py
from HCSR04.application.hc_usecase import HCUseCase

class HCController:
    def __init__(self, usecase: HCUseCase):
        self.usecase = usecase

    async def get_hc_data(self, event: bool = True):
        return await self.usecase.execute(event=event)
