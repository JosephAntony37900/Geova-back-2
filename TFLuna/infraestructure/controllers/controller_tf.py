# TFLuna/infraestructure/controllers/controller_tf.py
from TFLuna.application.tf_usecases import TFUseCase

class TFController:
    def __init__(self, usecase: TFUseCase):
        self.usecase = usecase

    async def get_tf_data(self, event: bool = False):
        return await self.usecase.execute(event=event)
