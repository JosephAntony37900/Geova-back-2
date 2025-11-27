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
        raw = await self.reader.read()  # ASYNC: Usa await para no bloquear I2C
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
        #exists = await self.repository.exists_by_project(data.id_project, online)
        #descomentar si se quiere limitar a 4 mediciones por proyecto
        #if exists:
        #    return {"msg": f"Ya existen 4 mediciones MPU6050 para el proyecto {data.id_project}"}

        self.publisher.publish(data)
        await self.repository.save(data, online)
        return {"msg": "Datos MPU6050 guardados correctamente"}

    async def update(self, sensor_id: int, data: SensorMPU):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición MPU con ID {sensor_id}", "success": False}

        # Mantener el project_id original
        data.id = sensor_id
        data.id_project = existing_record.id_project
        
        # PUT normal: resetear a medición simple
        data.is_dual_measurement = False
        data.measurement_count = 1
        
        self.publisher.publish(data)
        await self.repository.update(data, online)
        
        return {"msg": "Datos MPU actualizados correctamente", "success": True}

    async def update_dual(self, sensor_id: int, new_data: SensorMPU):
        online = await self.is_connected()
        existing_record = await self.repository.get_by_id(sensor_id, online)
        
        if not existing_record:
            return {"msg": f"No existe una medición MPU con ID {sensor_id}", "success": False}

        # Verificar si ya es dual completa (measurement_count = 2)
        if existing_record.is_dual_measurement and existing_record.measurement_count >= 2:
            return {
                "msg": f"La medición MPU ID {sensor_id} ya es dual completa. Use PUT normal para resetear.",
                "success": False
            }
        
        # Calcular promedios de todos los valores
        avg_ax = round((existing_record.ax + new_data.ax) / 2, 2)
        avg_ay = round((existing_record.ay + new_data.ay) / 2, 2)
        avg_az = round((existing_record.az + new_data.az) / 2, 2)
        avg_gx = round((existing_record.gx + new_data.gx) / 2, 2)
        avg_gy = round((existing_record.gy + new_data.gy) / 2, 2)
        avg_gz = round((existing_record.gz + new_data.gz) / 2, 2)
        avg_roll = round((existing_record.roll + new_data.roll) / 2, 2)
        avg_pitch = round((existing_record.pitch + new_data.pitch) / 2, 2)
        avg_apertura = round((existing_record.apertura + new_data.apertura) / 2, 2)
        
        # Crear datos actualizados con promedios
        updated_data = SensorMPU(
            id=existing_record.id,
            id_project=existing_record.id_project,
            ax=avg_ax,
            ay=avg_ay,
            az=avg_az,
            gx=avg_gx,
            gy=avg_gy,
            gz=avg_gz,
            roll=avg_roll,
            pitch=avg_pitch,
            apertura=avg_apertura,
            event=True,
            timestamp=new_data.timestamp,
            is_dual_measurement=True,
            measurement_count=2
        )
        
        self.publisher.publish(updated_data)
        await self.repository.update(updated_data, online)
        
        return {
            "msg": "Medición MPU dual completada correctamente",
            "success": True,
            "measurement_count": 2,
            "first_measurement": {
                "ax": existing_record.ax, "ay": existing_record.ay, "az": existing_record.az,
                "gx": existing_record.gx, "gy": existing_record.gy, "gz": existing_record.gz,
                "roll": existing_record.roll, "pitch": existing_record.pitch, "apertura": existing_record.apertura
            },
            "second_measurement": {
                "ax": new_data.ax, "ay": new_data.ay, "az": new_data.az,
                "gx": new_data.gx, "gy": new_data.gy, "gz": new_data.gz,
                "roll": new_data.roll, "pitch": new_data.pitch, "apertura": new_data.apertura
            },
            "averages": {
                "ax": avg_ax, "ay": avg_ay, "az": avg_az,
                "gx": avg_gx, "gy": avg_gy, "gz": avg_gz,
                "roll": avg_roll, "pitch": avg_pitch, "apertura": avg_apertura
            }
        }

    async def delete(self, project_id: int):
        online = await self.is_connected()
        has_records = await self.repository.has_any_record(project_id, online)
        
        if not has_records:
            return {"msg": f"No existe una medición MPU para el proyecto {project_id}", "success": False}

        await self.repository.delete(project_id, online)
        
        try:
            temp_data = SensorMPU(
                id_project=project_id,
                ax=0.0, ay=0.0, az=0.0,
                gx=0.0, gy=0.0, gz=0.0,
                roll=0.0, pitch=0.0, apertura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación MPU: {e}")
        
        return {"msg": "Medición MPU eliminada correctamente", "success": True}

    async def delete_by_id(self, record_id: int):
        online = await self.is_connected()
        record = await self.repository.get_by_id(record_id, online)
        
        if not record:
            return {"msg": f"No existe un registro MPU con ID {record_id}", "success": False}

        await self.repository.delete_by_id(record_id, online)
        
        try:
            temp_data = SensorMPU(
                id_project=record.id_project,
                ax=0.0, ay=0.0, az=0.0,
                gx=0.0, gy=0.0, gz=0.0,
                roll=0.0, pitch=0.0, apertura=0.0,
                event=True
            )
            temp_data.__dict__["_action"] = "delete_by_id"
            self.publisher.publish(temp_data)
        except Exception as e:
            print(f"Error publicando evento de eliminación MPU: {e}")
        
        return {"msg": f"Registro MPU ID {record_id} eliminado correctamente", "success": True}

    async def get_by_project_id(self, project_id: int) -> SensorMPU | None:
        online = await self.is_connected()
        return await self.repository.get_by_project_id(project_id, online)