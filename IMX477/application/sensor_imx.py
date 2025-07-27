# IMX477/application/sensor_imx.py
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.ports.mqtt_publisher import MQTTPublisher

class IMXUseCase:
    def __init__(self, reader, repository: IMXRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, resolution="640x480", event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorIMX477(id_project=project_id, resolution=resolution, event=event, **raw)
        self.publisher.publish(data)

        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorIMX477):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existen 4 mediciones IMX477 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos IMX477 guardados correctamente"}

    async def update(self, project_id: int, data: SensorIMX477):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición IMX477 para el proyecto {project_id}", "success": False}
        
        # Actualizar el project_id del data con el del parámetro
        data.id_project = project_id
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos IMX477 actualizados correctamente", "success": True}

    async def delete(self, project_id: int):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición IMX477 para el proyecto {project_id}", "success": False}
        
        await self.repository.delete(project_id, online)
        
        # Publicar evento de eliminación
        try:
            temp_data = SensorIMX477(
                id_project=project_id,
                resolution="640x480",
                luminosidad_promedio=0.0,
                nitidez_score=0.0,
                laser_detectado=False,
                calidad_frame=0.0,
                probabilidad_confiabilidad=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación IMX: {e}")
        
        return {"msg": "Medición IMX477 eliminada correctamente", "success": True}

    async def get_by_project_id(self, project_id: int):
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)