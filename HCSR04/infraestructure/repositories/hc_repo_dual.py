# HCSR04/infraestructure/repositories/hc_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.infraestructure.repositories.schemas_sqlalchemy import SensorHCModel

class DualHCSensorRepository(HCSensorRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: HCSensorData, online: bool):
        async with self.local_factory() as session_local:
            local_model = SensorHCModel(**sensor_data.dict(), synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorHCModel(**sensor_data.dict(), synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def update(self, sensor_data: HCSensorData, online: bool):
        async with self.local_factory() as session_local:
            # Actualizar en local
            stmt = (
                update(SensorHCModel)
                .where(SensorHCModel.id_project == sensor_data.id_project)
                .values(
                    distancia_cm=sensor_data.distancia_cm,
                    distancia_m=sensor_data.distancia_m,
                    tiempo_vuelo_us=sensor_data.tiempo_vuelo_us,
                    event=sensor_data.event,
                    timestamp=sensor_data.timestamp,
                    synced=online
                )
            )
            await session_local.execute(stmt)
            await session_local.commit()

        # Si hay internet, actualizar también en remoto
        if online:
            async with self.remote_factory() as session_remote:
                stmt = (
                    update(SensorHCModel)
                    .where(SensorHCModel.id_project == sensor_data.id_project)
                    .values(
                        distancia_cm=sensor_data.distancia_cm,
                        distancia_m=sensor_data.distancia_m,
                        tiempo_vuelo_us=sensor_data.tiempo_vuelo_us,
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
            stmt = delete(SensorHCModel).where(SensorHCModel.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        # Si hay internet, eliminar también de remoto
        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorHCModel).where(SensorHCModel.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorHCModel).where(SensorHCModel.id_project == project_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_project_id(self, project_id: int, online: bool) -> HCSensorData | None:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorHCModel).where(SensorHCModel.id_project == project_id)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                return HCSensorData(**record.as_dict())
            return None