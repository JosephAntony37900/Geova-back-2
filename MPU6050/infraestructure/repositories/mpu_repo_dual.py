# MPU6050/infraestructure/repositories/mpu_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
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