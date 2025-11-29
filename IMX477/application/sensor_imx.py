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
        raw = await self.reader.read()  # ASYNC: Usa await para no bloquear
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
        #exists = await self.repository.exists_by_project(data.id_project, online)
        #descomentar si se quiere limitar a 4 mediciones por proyecto
        #if exists:
        #    return {"msg": f"Ya existen 4 mediciones IMX477 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos IMX477 guardados correctamente"}

    async def update(self, sensor_id: int, data: SensorIMX477):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición con ID {sensor_id}", "success": False}

        data.id = sensor_id
        data.id_project = existing_record.id_project
        
        data.is_dual_measurement = False
        data.measurement_count = 1
        data.avg_luminosidad = None
        data.avg_nitidez = None
        data.avg_calidad = None
        data.avg_probabilidad = None
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos IMX477 actualizados correctamente", "success": True}

    async def update_dual(self, sensor_id: int, new_data: SensorIMX477):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición con ID {sensor_id}", "success": False}

        if existing_record.is_dual_measurement and existing_record.measurement_count >= 2:
            return {
                "msg": f"La medición ID {sensor_id} ya es dual completa. Use PUT normal para resetear.",
                "success": False
            }
        
        avg_luminosidad = round((existing_record.luminosidad_promedio + new_data.luminosidad_promedio) / 2, 2)
        avg_nitidez = round((existing_record.nitidez_score + new_data.nitidez_score) / 2, 2)
        avg_calidad = round((existing_record.calidad_frame + new_data.calidad_frame) / 2, 2)
        avg_probabilidad = round((existing_record.probabilidad_confiabilidad + new_data.probabilidad_confiabilidad) / 2, 2)
        
        laser_combinado = existing_record.laser_detectado or new_data.laser_detectado
        
        updated_data = SensorIMX477(
            id=existing_record.id,
            id_project=existing_record.id_project,
            resolution=existing_record.resolution,
            luminosidad_promedio=avg_luminosidad,
            nitidez_score=avg_nitidez,
            laser_detectado=laser_combinado,
            calidad_frame=avg_calidad,
            probabilidad_confiabilidad=avg_probabilidad,
            event=True,
            timestamp=new_data.timestamp,
            is_dual_measurement=True,
            measurement_count=2,
            avg_luminosidad=avg_luminosidad,
            avg_nitidez=avg_nitidez,
            avg_calidad=avg_calidad,
            avg_probabilidad=avg_probabilidad
        )
        
        self.publisher.publish(updated_data)
        await self.repository.update(updated_data, online)
        
        return {
            "msg": "Medición dual IMX477 completada correctamente",
            "success": True,
            "measurement_count": 2,
            "first_measurement": {
                "luminosidad": existing_record.luminosidad_promedio,
                "nitidez": existing_record.nitidez_score,
                "calidad": existing_record.calidad_frame,
                "probabilidad": existing_record.probabilidad_confiabilidad
            },
            "second_measurement": {
                "luminosidad": new_data.luminosidad_promedio,
                "nitidez": new_data.nitidez_score,
                "calidad": new_data.calidad_frame,
                "probabilidad": new_data.probabilidad_confiabilidad
            },
            "averages": {
                "avg_luminosidad": avg_luminosidad,
                "avg_nitidez": avg_nitidez,
                "avg_calidad": avg_calidad,
                "avg_probabilidad": avg_probabilidad,
                "laser_detectado": laser_combinado
            }
        }

    async def delete(self, project_id: int):
        online = await self.is_connected()
        has_records = await self.repository.has_any_record(project_id, online)
        
        if not has_records:
            return {"msg": f"No existe una medición IMX477 para el proyecto {project_id}", "success": False}

        await self.repository.delete(project_id, online)
        
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

    async def delete_by_id(self, record_id: int):
        online = await self.is_connected()
        record = await self.repository.get_by_id(record_id, online)
        
        if not record:
            return {"msg": f"No existe un registro con ID {record_id}", "success": False}

        await self.repository.delete_by_id(record_id, online)
        
        try:
            temp_data = SensorIMX477(
                id_project=record.id_project,
                resolution="640x480",
                luminosidad_promedio=0.0,
                nitidez_score=0.0,
                laser_detectado=False,
                calidad_frame=0.0,
                probabilidad_confiabilidad=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete_by_id"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación IMX: {e}")
        
        return {"msg": f"Registro IMX477 ID {record_id} eliminado correctamente", "success": True}

    async def get_by_project_id(self, project_id: int):
        # Primero intentar local (siempre rápido), luego remoto si hay conexión
        try:
            # Intentar local primero - siempre disponible y rápido
            local_data = await self.repository.get_by_project_id(project_id, online=False)
            if local_data:
                return local_data
            
            # Si no hay datos locales, intentar remoto
            online = await self.is_connected()
            if online:
                return await self.repository.get_by_project_id(project_id, online=True)
            return local_data
        except Exception as e:
            print(f"Error en get_by_project_id IMX477: {e}")
            return None