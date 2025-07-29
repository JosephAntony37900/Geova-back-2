# HCSR04/application/hc_usecase.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher
from typing import List

class HCUseCase:
    def __init__(self, reader, repository: HCSensorRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected

    async def execute(self, project_id=1, event=False):
        try:
            raw = await self.reader.read_async()
            
            if not raw or 'distancia_cm' not in raw:
                return None

            # Crear HCSensorData con los datos recibidos
            data = HCSensorData(
                id_project=project_id, 
                distancia_cm=raw['distancia_cm'],
                event=event
            )
            
            # Solo publicar a MQTT si hay conexión a internet
            try:
                if await self.is_connected():
                    self.publisher.publish(data)
                    print(f"📡 HC-SR04: Publicado a MQTT - {data.distancia_cm} cm")
            except Exception as e:
                print(f"🔵 HC-SR04: Error al publicar a MQTT - {e}")
            
            # Solo guardar en BD si event=True
            if event:
                try:
                    online = await self.is_connected()
                    await self.repository.save(data, online)
                    print(f"💾 HC-SR04: Guardado en BD - {data.distancia_cm} cm")
                except Exception as e:
                    print(f"🔵 HC-SR04: Error al guardar datos - {e}")

            return data
            
        except Exception as e:
            print(f"🔵 HC-SR04: Error en execute - {e}")
            return None

    async def create(self, data: HCSensorData):
        if not data.event:
            return {"msg": "No se almacenó porque event es False"}

        try:
            online = await self.is_connected()
            
            # Publicar a MQTT solo si hay conexión
            if online:
                self.publisher.publish(data)
                
            await self.repository.save(data, online)
            return {"msg": "Datos guardados correctamente", "success": True}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al crear - {e}")
            return {"msg": f"Error al guardar datos: {e}", "success": False}

    async def update(self, project_id: int, data: HCSensorData):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existe ninguna medición HC-SR04 para el proyecto {project_id}", "success": False}
        
        data.id_project = project_id
        
        try:
            # Publicar a MQTT solo si hay conexión
            if online:
                self.publisher.publish(data)
                
            await self.repository.update_all_by_project(project_id, data, online)
            return {"msg": "Datos HC-SR04 actualizados correctamente", "success": True}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al actualizar - {e}")
            return {"msg": f"Error al actualizar datos: {e}", "success": False}

    async def delete(self, project_id: int):
        online = await self.is_connected()
        exists = await self.repository.exists_by_project(project_id, online)
        
        if not exists:
            return {"msg": f"No existen mediciones HC-SR04 para el proyecto {project_id}", "success": False}
        
        try:
            await self.repository.delete_all_by_project(project_id, online)
            
            # Publicar evento de eliminación solo si hay conexión
            try:
                if online:
                    temp_data = HCSensorData(
                        id_project=project_id,
                        distancia_cm=0,
                        event=True
                    )
                    temp_data.__dict__["_action"] = "delete"
                    self.publisher.publish(temp_data)
            except Exception as e:
                print(f"🔵 HC-SR04: Error publicando evento de eliminación - {e}")
            
            return {"msg": "Todas las mediciones HC-SR04 del proyecto eliminadas correctamente", "success": True}
        except Exception as e:
            print(f"🔵 HC-SR04: Error al eliminar - {e}")
            return {"msg": f"Error al eliminar datos: {e}", "success": False}

    async def get_by_project_id(self, project_id: int) -> List[HCSensorData]:
        try:
            online = await self.is_connected()
            return await self.repository.get_all_by_project_id(project_id, online)
        except Exception as e:
            print(f"🔵 HC-SR04: Error al obtener datos - {e}")
            return []

    async def get_latest_by_project_id(self, project_id: int) -> HCSensorData | None:
        try:
            online = await self.is_connected()
            return await self.repository.get_latest_by_project_id(project_id, online)
        except Exception as e:
            print(f"🔵 HC-SR04: Error al obtener datos - {e}")
            return None