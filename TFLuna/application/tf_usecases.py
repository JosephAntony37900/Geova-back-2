# TFLuna/application/tf_usecases.py
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.ports.mqtt_publisher import MQTTPublisher

class TFUseCase:
    def __init__(self, reader, repository: TFLunaRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=False):  # Cambiar event=False por defecto
        """
        Lee datos del sensor. 
        - Si event=False: Solo retorna los datos para monitoreo (no persiste)
        - Si event=True: Persiste en base de datos
        """
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorTF(id_project=project_id, event=event, **raw)
        
        # Siempre publico a MQTT para monitoreo
        self.publisher.publish(data)

        # Solo guardo en BD si event=True (peticiones POST del frontend)
        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorTF):
        """
        Método específico para crear mediciones desde el frontend
        """
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def get_by_project_id(self, project_id: int) -> SensorTF | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)