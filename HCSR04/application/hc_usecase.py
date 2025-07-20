# HCSR04/application/hc_usecase.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher
from HCSR04.infraestructure.ble.hc_ble_reader import HCBLEReader
from core.connectivity import is_connected
from core.config import get_engine, get_remote_engine

class HCUseCase:
    def __init__(self, reader: HCBLEReader, repository: HCSensorRepository, publisher: MQTTPublisher):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.local_engine = get_engine()
        self.remote_engine = None

        if is_connected():
            try:
                self.remote_engine = get_remote_engine()
            except Exception as e:
                print(f"[⚠️] Error al conectar con MongoDB remoto: {e}")
                self.remote_engine = None

    async def execute(self, project_id=1, event=True):
        raw = self.reader.read()
        if not raw:
            return None

        data = HCSensorData(id_project=project_id, event=event, **raw)

       
        self.publisher.publish(data)

        if event:
            
            await self.repository.save(data, engine=self.local_engine)

            
            if self.remote_engine:
                await self.repository.save(data, engine=self.remote_engine)

        return data
