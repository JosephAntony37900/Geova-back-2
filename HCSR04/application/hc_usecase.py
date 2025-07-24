# HCSR04/application/hc_usecases.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher

class HCUseCase:
    def __init__(self, reader, repository: HCSensorRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = HCSensorData(id_project=project_id, event=event, **raw)
        
        # Solo publicar, NO guardar
        self.publisher.publish(data)

        return data

    async def create(self, data: HCSensorData):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición HC-SR04 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def update(self, project_id: int, data: HCSensorData):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición HC-SR04 para el proyecto {project_id}", "success": False}
        
        # Actualizar el project_id del data con el del parámetro
        data.id_project = project_id
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos HC-SR04 actualizados correctamente", "success": True}

    async def delete(self, project_id: int):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición HC-SR04 para el proyecto {project_id}", "success": False}
        
        await self.repository.delete(project_id, online)
        
        # Publicar evento de eliminación
        try:
            # Crear un objeto temporal para publicar el evento
            temp_data = HCSensorData(
                id_project=project_id,
                distancia_cm=0,
                distancia_m=0.0,
                tiempo_vuelo_us=0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"  # Agregar metadato
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación HC-SR04: {e}")
        
        return {"msg": "Medición HC-SR04 eliminada correctamente", "success": True}

    async def get_by_project_id(self, project_id: int) -> HCSensorData | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)
