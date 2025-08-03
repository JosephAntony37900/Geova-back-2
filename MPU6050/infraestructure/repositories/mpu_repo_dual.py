# MPU6050/infraestructure/repositories/mpu_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import SensorMPUModel
from datetime import datetime
from typing import List, Optional

class DualMPURepository(MPURepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorMPU, online: bool):
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)
        
        async with self.local_factory() as session_local:
            try:
                local_model = SensorMPUModel(**data_dict, synced=online)
                session_local.add(local_model)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    remote_model = SensorMPUModel(**data_dict, synced=True)
                    session_remote.add(remote_model)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def update(self, sensor_data: SensorMPU, online: bool):
        if sensor_data.id is None:
            raise ValueError("Falta el ID para actualizar el registro MPU")

        update_values = {
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
            'is_dual_measurement': sensor_data.is_dual_measurement,
            'measurement_count': sensor_data.measurement_count,
            'synced': online
        }

        async with self.local_factory() as session_local:
            try:
                stmt = update(SensorMPUModel).where(
                    SensorMPUModel.id == sensor_data.id
                ).values(**update_values)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    remote_values = update_values.copy()
                    remote_values['synced'] = True
                    stmt = update(SensorMPUModel).where(
                        SensorMPUModel.id == sensor_data.id
                    ).values(**remote_values)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete_by_id(self, record_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorMPUModel).where(SensorMPUModel.id == record_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorMPUModel).where(SensorMPUModel.id == record_id)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(func.count()).select_from(SensorMPUModel).where(
                SensorMPUModel.id_project == project_id
            )
            result = await session.execute(stmt)
            count = result.scalar()
            return count >= 4

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

    async def has_any_record(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = select(func.count()).select_from(SensorMPUModel).where(
                    SensorMPUModel.id_project == project_id
                )
                result = await session.execute(stmt)
                count = result.scalar()
                return count > 0
            except Exception as e:
                await session.rollback()
                raise e
                
    async def get_by_id(self, record_id: int, online: bool) -> Optional[SensorMPU]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = select(SensorMPUModel).where(SensorMPUModel.id == record_id)
                result = await session.execute(stmt)
                record = result.scalars().first()
                return SensorMPU(**record.as_dict()) if record else None
            except Exception as e:
                await session.rollback()
                raise e