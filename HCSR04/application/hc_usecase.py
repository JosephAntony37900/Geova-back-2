# HCSR04/application/hc_usecase.py
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
        """
        Ejecuta la lectura del sensor HC-SR04 vía BLE
        Devuelve None si no hay datos disponibles (sin conexión BLE)
        """
        try:
            # Usar el método asíncrono para evitar el error del event loop
            raw = await self.reader.read_async()
            
            # Si no hay datos (sin conexión BLE), devolver None
            if not raw:
                return None

            # Crear objeto de datos solo si hay datos reales
            data = HCSensorData(id_project=project_id, event=event, **raw)
            
            # Solo publicar si tenemos datos reales
            try:
                self.publisher.publish(data)
            except Exception as e:
                print(f"🔵 HC-SR04: Error al publicar datos - {e}")

            return data
            
        except Exception as e:
            print(f"🔵 HC-SR04: Error en execute - {e}")
            return None

    async def create(self, data: HCSensorData):
        """Crear nueva medición HC-SR04"""
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        online = await self.is_connected()
        exists = await self.repository.exists_by_project(data.id_project, online)

        if exists:
            return {"msg": f"Ya existe una medición HC-SR04 para el proyecto {data.id_project}"}

        try:
            self.publisher.publish(data)
            await self.repository.save(data, online)
            return {"msg": "Datos guardados correctamente"}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al crear - {e}")
            return {"msg": f"Error al guardar datos: {e}"}

    async def update(self, project_id: int, data: HCSensorData):
        """Actualizar medición HC-SR04 existente"""
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición HC-SR04 para el proyecto {project_id}", "success": False}
        
        # Actualizar el project_id del data con el del parámetro
        data.id_project = project_id
        
        try:
            self.publisher.publish(data)
            await self.repository.update(data, online)
            return {"msg": "Datos HC-SR04 actualizados correctamente", "success": True}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al actualizar - {e}")
            return {"msg": f"Error al actualizar datos: {e}", "success": False}

    async def delete(self, project_id: int):
        """Eliminar medición HC-SR04"""
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe una medición HC-SR04 para el proyecto {project_id}", "success": False}
        
        try:
            await self.repository.delete(project_id, online)
            
            # Publicar evento de eliminación
            try:
                temp_data = HCSensorData(
                    id_project=project_id,
                    distancia_cm=0,
                    event=True
                )
                temp_data.__dict__["_action"] = "delete"  # Agregar metadato
                self.publisher.publish(temp_data)
            except Exception as e:
                print(f"🔵 HC-SR04: Error publicando evento de eliminación - {e}")
            
            return {"msg": "Medición HC-SR04 eliminada correctamente", "success": True}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al eliminar - {e}")
            return {"msg": f"Error al eliminar datos: {e}", "success": False}

    async def get_by_project_id(self, project_id: int) -> HCSensorData | None:
        """Obtener medición HC-SR04 por ID de proyecto"""
        try:
            online = await self.is_connected()
            return await self.repository.get_by_project_id(project_id, online)
        except Exception as e:
            print(f"🔵 HC-SR04: Error al obtener datos - {e}")
            return None