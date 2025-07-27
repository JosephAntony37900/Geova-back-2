# MPU6050/infraestructure/repositories/mpu_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import SensorMPUModel
from datetime import datetime
from typing import List

class DualMPURepository(MPURepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorMPU, online: bool):
        # Crear diccionario sin el ID para que sea autoincremental
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)  # Remover id si existe
        
        async with self.local_factory() as session_local:
            local_model = SensorMPUModel(**data_dict, synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorMPUModel(**data_dict, synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def update(self, sensor_data: SensorMPU, online: bool):
        if sensor_data.id is None:
            raise ValueError("Falta el ID para actualizar el registro MPU")

        # Preparar datos sin el ID para la actualización
        update_data = {
            'id_project': sensor_data.id_project,
            'ax': sensor_data.ax,
            'ay': sensor_data.ay,
            'az': sensor_data.az,
            'gx': sensor_data.gx,
            'gy': sensor_data.gy,
            'gz': sensor_data.gz,
            'roll': sensor_data.roll,
            'pitch': sensor_data.pitch,
            'apertura': sensor_data.apertura,
            'event': sensor_data.event,
            'timestamp': sensor_data.timestamp,
            'synced': online
        }

        async with self.local_factory() as session_local:
            stmt = (
                update(SensorMPUModel)
                .where(SensorMPUModel.id == sensor_data.id)
                .values(**update_data)
            )
            await session_local.execute(stmt)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                update_data['synced'] = True
                stmt = (
                    update(SensorMPUModel)
                    .where(SensorMPUModel.id == sensor_data.id)
                    .values(**update_data)
                )
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(func.count()).select_from(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
            result = await session.execute(stmt)
            count = result.scalar()
            return count >= 4  # Ya existen 4 o más registros

    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorMPU]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = (
                select(SensorMPUModel)
                .where(SensorMPUModel.id_project == project_id)
                .order_by(SensorMPUModel.timestamp.desc())
                .limit(4)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [SensorMPU(**r.as_dict()) for r in records]
