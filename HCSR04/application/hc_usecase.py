# HCSR04/application/hc_usecase.py
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher
from typing import List
import asyncio

class HCUseCase:
    def __init__(self, reader, repository: HCSensorRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.publisher = publisher
        self.is_connected = is_connected
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3

    async def execute(self, project_id=1, event=False):
        try:
            raw = await self.reader.read_async()
            
            if not raw or 'distancia_cm' not in raw:
                self.consecutive_errors += 1
                if self.consecutive_errors <= self.max_consecutive_errors:
                    print(f"🟡 HC-SR04: Sin datos del ESP32 (intento {self.consecutive_errors}/{self.max_consecutive_errors})")
                return None

            self.consecutive_errors = 0

            distance = raw['distancia_cm']
            if distance <= 0 or distance > 400:
                print(f"🟡 HC-SR04: Distancia fuera de rango: {distance} cm")
                return None

            data = HCSensorData(
                id_project=project_id, 
                distancia_cm=distance,
                event=event
            )
            
            # ✅ SIEMPRE publicar a MQTT (igual que TF-Luna)
            self.publisher.publish(data)
            
            # ✅ SOLO guardar en BD si event=True (igual que TF-Luna)
            if event:
                try:
                    online = await self.is_connected()
                    await self.repository.save(data, online)
                    print(f"💾 HC-SR04: Guardado - {data.distancia_cm:.1f} cm")
                except Exception as e:
                    print(f"🔴 HC-SR04: Error guardando en BD - {e}")

            return data
            
        except Exception as e:
            self.consecutive_errors += 1
            if self.consecutive_errors <= self.max_consecutive_errors:
                print(f"🔴 HC-SR04: Error en execute - {e}")
            return None

    async def create(self, data: HCSensorData):
        if not data.event:
            return {"msg": "No se almacenó porque event es False", "success": True}

        try:
            online = await self.is_connected()
            
            # Publicar a MQTT
            self.publisher.publish(data)
                
            await self.repository.save(data, online)
            return {"msg": "Datos guardados correctamente", "success": True}
        except Exception as e:
            print(f"🔴 HC-SR04: Error al crear - {e}")
            return {"msg": f"Error al guardar datos: {str(e)}", "success": False}

    async def update(self, project_id: int, data: HCSensorData):
        try:
            online = await self.is_connected()
            exists = await self.repository.exists_by_project(project_id, online)
            
            if not exists:
                return {"msg": f"No existe ninguna medición HC-SR04 para el proyecto {project_id}", "success": False}
            
            data.id_project = project_id
            
            # Publicar a MQTT
            self.publisher.publish(data)
                
            await self.repository.update_all_by_project(project_id, data, online)
            return {"msg": "Datos HC-SR04 actualizados correctamente", "success": True}
        except Exception as e:
            print(f"🔴 HC-SR04: Error al actualizar - {e}")
            return {"msg": f"Error al actualizar datos: {str(e)}", "success": False}

    async def delete(self, project_id: int):
        try:
            online = await self.is_connected()
            exists = await self.repository.exists_by_project(project_id, online)
            
            if not exists:
                return {"msg": f"No existen mediciones HC-SR04 para el proyecto {project_id}", "success": False}
            
            await self.repository.delete_all_by_project(project_id, online)
            
            # Publicar evento de eliminación a MQTT
            try:
                temp_data = HCSensorData(
                    id_project=project_id,
                    distancia_cm=0,
                    event=True
                )
                temp_data.__dict__["_action"] = "delete"
                self.publisher.publish(temp_data)
            except Exception as e:
                print(f"🟡 HC-SR04: Error publicando evento eliminación - {e}")
            
            return {"msg": "Todas las mediciones HC-SR04 del proyecto eliminadas correctamente", "success": True}
        except Exception as e:
            print(f"🔴 HC-SR04: Error al eliminar - {e}")
            return {"msg": f"Error al eliminar datos: {str(e)}", "success": False}

    async def get_by_project_id(self, project_id: int) -> List[HCSensorData]:
        try:
            # Primero intentar local (siempre rápido)
            local_data = await self.repository.get_all_by_project_id(project_id, online=False)
            if local_data:
                return local_data
            
            # Si no hay datos locales, intentar remoto
            online = await self.is_connected()
            if online:
                return await self.repository.get_all_by_project_id(project_id, online=True)
            return local_data
        except Exception as e:
            print(f"🔴 HC-SR04: Error al obtener datos por proyecto - {e}")
            return []

    async def get_latest_by_project_id(self, project_id: int) -> HCSensorData | None:
        try:
            # Primero intentar local (siempre rápido)
            local_data = await self.repository.get_latest_by_project_id(project_id, online=False)
            if local_data:
                return local_data
            
            # Si no hay datos locales, intentar remoto
            online = await self.is_connected()
            if online:
                return await self.repository.get_latest_by_project_id(project_id, online=True)
            return local_data
        except Exception as e:
            print(f"🔴 HC-SR04: Error al obtener último dato - {e}")
            return None

    def get_connection_status(self) -> dict:
        return {
            "reader_connected": hasattr(self.reader, 'is_connected') and self.reader.is_connected,
            "consecutive_errors": self.consecutive_errors,
            "max_errors": self.max_consecutive_errors
        }