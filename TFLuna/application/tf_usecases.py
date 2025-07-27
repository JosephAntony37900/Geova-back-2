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

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorTF(id_project=project_id, event=event, **raw)
        
        self.publisher.publish(data)

        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorTF):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existen 4 mediciones para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def update(self, project_id: int, data: SensorTF):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición para el proyecto {project_id}", "success": False}

        # Actualizar el project_id del data con el del parámetro
        data.id_project = project_id
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos actualizados correctamente", "success": True}

    async def delete(self, project_id: int):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición para el proyecto {project_id}", "success": False}

        await self.repository.delete(project_id, online)
        
        # Publicar evento de eliminación
        delete_event = {"action": "delete", "project_id": project_id, "sensor": "tfluna"}
        try:
            import json
            from TFLuna.domain.entities.sensor_tf import SensorTFLuna
            # Crear un objeto temporal para publicar el evento
            temp_data = SensorTFLuna(
                id_project=project_id,
                distancia_cm=0,
                distancia_m=0.0,
                fuerza_senal=0,
                temperatura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"  # Agregar metadato
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación: {e}")
        
        return {"msg": "Medición eliminada correctamente", "success": True}

    async def get_by_project_id(self, project_id: int) -> SensorTF | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)