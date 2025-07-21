from sqlalchemy import select
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.repositories.schemas_sqlalchemy import SensorIMX477Model

class DualIMXRepository(IMXRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorIMX477, online: bool):
        async with self.local_factory() as session_local:
            local_model = SensorIMX477Model(**sensor_data.dict(), synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorIMX477Model(**sensor_data.dict(), synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_project_id(self, project_id: int, online: bool) -> SensorIMX477 | None:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                return SensorIMX477(**record.as_dict())
            return None
