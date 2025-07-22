# MPU6050/application/mpu_usecase.py
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.ports.mpu_publisher import MPUPublisher

class MPUUseCase:
    def __init__(self, reader, repository: MPURepository, publisher: MPUPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=False):
        raw = self.reader.read()
        if not raw:
            return None

        data = SensorMPU(id_project=project_id, event=event, **raw)
        self.publisher.publish(data)

        if event:
            online = await self.is_connected()
            await self.repository.save(data, online)

        return data

    async def create(self, data: SensorMPU):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición con el sensor de inclinación MPU6050 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos guardados correctamente"}

    async def update(self, project_id: int, data: SensorMPU):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición MPU6050 para el proyecto {project_id}", "success": False}

        # Actualizar el project_id del data con el del parámetro
        data.id_project = project_id
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos MPU6050 actualizados correctamente", "success": True}

    async def delete(self, project_id: int):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición MPU6050 para el proyecto {project_id}", "success": False}

        await self.repository.delete(project_id, online)
        
        # Publicar evento de eliminación
        try:
            from MPU6050.domain.entities.sensor_mpu import SensorMPU
            # Crear un objeto temporal para publicar el evento
            temp_data = SensorMPU(
                id_project=project_id,
                ax=0.0, ay=0.0, az=0.0,
                gx=0.0, gy=0.0, gz=0.0,
                roll=0.0, pitch=0.0, apertura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"  # Agregar metadato
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación MPU: {e}")
        
        return {"msg": "Medición MPU6050 eliminada correctamente", "success": True}

    async def get_by_project_id(self, project_id: int) -> SensorMPU | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)