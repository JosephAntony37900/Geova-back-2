# MPU6050/infraestructure/repositories/mpu_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from MPU6050.domain.repositories.mpu_repository import MPURepository
from MPU6050.domain.entities.sensor_mpu import SensorMPU
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import SensorMPUModel
from datetime import datetime

class DualMPURepository(MPURepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorMPU, online: bool):
        async with self.local_factory() as session_local:
            local_model = SensorMPUModel(**sensor_data.dict(), synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorMPUModel(**sensor_data.dict(), synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def update(self, sensor_data: SensorMPU, online: bool):
        async with self.local_factory() as session_local:
            # Actualizar en local
            stmt = (
                update(SensorMPUModel)
                .where(SensorMPUModel.id_project == sensor_data.id_project)
                .values(
                    ax=sensor_data.ax, ay=sensor_data.ay, az=sensor_data.az,
                    gx=sensor_data.gx, gy=sensor_data.gy, gz=sensor_data.gz,
                    roll=sensor_data.roll, pitch=sensor_data.pitch,
                    apertura=sensor_data.apertura,
                    event=sensor_data.event,
                    timestamp=sensor_data.timestamp,
                    synced=online  # Marcar como no sincronizado si no hay internet
                )
            )
            await session_local.execute(stmt)
            await session_local.commit()

        # Si hay internet, actualizar también en remoto
        if online:
            async with self.remote_factory() as session_remote:
                stmt = (
                    update(SensorMPUModel)
                    .where(SensorMPUModel.id_project == sensor_data.id_project)
                    .values(
                        ax=sensor_data.ax, ay=sensor_data.ay, az=sensor_data.az,
                        gx=sensor_data.gx, gy=sensor_data.gy, gz=sensor_data.gz,
                        roll=sensor_data.roll, pitch=sensor_data.pitch,
                        apertura=sensor_data.apertura,
                        event=sensor_data.event,
                        timestamp=sensor_data.timestamp,
                        synced=True
                    )
                )
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            # Eliminar de local
            stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        # Si hay internet, eliminar también de remoto
        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_project_id(self, project_id: int, online: bool) -> SensorMPU | None:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorMPUModel).where(SensorMPUModel.id_project == project_id)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                return SensorMPU(**record.as_dict())
            return None