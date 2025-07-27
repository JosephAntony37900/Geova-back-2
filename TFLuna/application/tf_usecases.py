# TFLuna/application/tf_usecases.py
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.ports.mqtt_publisher import MQTTPublisher

class TFUseCase:
    def __init__(self, reader, repository: TFLunaRepository, publisher: MQTTPublisher, is_connected):
        self.reader = reader
        self.repository = repository
        self.is_connected = is_connected
        self.publisher = publisher

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

    async def update(self, sensor_id: int, data: SensorTF):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición con ID {sensor_id}", "success": False}

        # Mantener el project_id original
        data.id = sensor_id
        data.id_project = existing_record.id_project
        
        # PUT normal: resetear a medición simple
        data.is_dual_measurement = False
        data.measurement_count = 1
        data.total_distance_cm = None
        data.total_distance_m = None
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos actualizados correctamente", "success": True}

    async def update_dual(self, sensor_id: int, new_data: SensorTF):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición con ID {sensor_id}", "success": False}

        # Verificar si ya es dual completa (measurement_count = 2)
        if existing_record.is_dual_measurement and existing_record.measurement_count >= 2:
            return {
                "msg": f"La medición ID {sensor_id} ya es dual completa. Use PUT normal para resetear.",
                "success": False
            }

        # Calcular medición dual
        MARGIN_CM = 7.5
        total_distance_cm = existing_record.distancia_cm + new_data.distancia_cm - MARGIN_CM
        total_distance_m = round(total_distance_cm / 100, 2)
        
        if total_distance_m > 16.0:
            return {
                "msg": f"La distancia total ({total_distance_m}m) excede el límite máximo de 16m",
                "success": False
            }
        
        # Calcular promedios
        avg_fuerza_senal = round((existing_record.fuerza_senal + new_data.fuerza_senal) / 2)
        avg_temperatura = round((existing_record.temperatura + new_data.temperatura) / 2, 2)
        
        # Crear datos actualizados
        updated_data = SensorTF(
            id=existing_record.id,
            id_project=existing_record.id_project,
            distancia_cm=int(total_distance_cm),
            distancia_m=total_distance_m,
            fuerza_senal=avg_fuerza_senal,
            temperatura=avg_temperatura,
            event=True,
            timestamp=new_data.timestamp,
            is_dual_measurement=True,
            measurement_count=2,
            total_distance_cm=int(total_distance_cm),
            total_distance_m=total_distance_m
        )
        
        self.publisher.publish(updated_data)
        await self.repository.update(updated_data, online)
        
        return {
            "msg": "Medición dual completada correctamente",
            "success": True,
            "measurement_count": 2,
            "first_measurement_m": round(existing_record.distancia_cm / 100, 2),
            "second_measurement_m": round(new_data.distancia_cm / 100, 2),
            "total_distance_m": total_distance_m,
            "margin_applied_cm": MARGIN_CM,
            "avg_signal_strength": avg_fuerza_senal,
            "avg_temperature": avg_temperatura
        }

    async def delete(self, project_id: int):
        online = await self.is_connected()
        has_records = await self.repository.has_any_record(project_id, online)
        
        if not has_records:
            return {"msg": f"No existe una medición para el proyecto {project_id}", "success": False}

        await self.repository.delete(project_id, online)
        
        try:
            temp_data = SensorTF(
                id_project=project_id,
                distancia_cm=0,
                distancia_m=0.0,
                fuerza_senal=0,
                temperatura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación: {e}")
        
        return {"msg": "Medición eliminada correctamente", "success": True}

    async def delete_by_id(self, record_id: int):
        online = await self.is_connected()
        record = await self.repository.get_by_id(record_id, online)
        
        if not record:
            return {"msg": f"No existe un registro con ID {record_id}", "success": False}

        await self.repository.delete_by_id(record_id, online)
        
        try:
            temp_data = SensorTF(
                id_project=record.id_project,
                distancia_cm=0,
                distancia_m=0.0,
                fuerza_senal=0,
                temperatura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete_by_id"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación: {e}")
        
        return {"msg": f"Registro ID {record_id} eliminado correctamente", "success": True}

    async def get_by_project_id(self, project_id: int) -> SensorTF | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)