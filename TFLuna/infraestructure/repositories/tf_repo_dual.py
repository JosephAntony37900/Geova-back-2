# TFLuna/infraestructure/repositories/tf_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.infraestructure.repositories.schemas_sqlalchemy import SensorTFModel
from datetime import datetime
import uuid

class DualTFLunaRepository(TFLunaRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorTFLuna, online: bool):
        async with self.local_factory() as session_local:
            local_model = SensorTFModel(**sensor_data.dict(), synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorTFModel(**sensor_data.dict(), synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def update(self, sensor_data: SensorTFLuna, online: bool):
        async with self.local_factory() as session_local:
            # Actualizar en local
            stmt = (
                update(SensorTFModel)
                .where(SensorTFModel.id_project == sensor_data.id_project)
                .values(
                    distancia_cm=sensor_data.distancia_cm,
                    distancia_m=sensor_data.distancia_m,
                    fuerza_senal=sensor_data.fuerza_senal,
                    temperatura=sensor_data.temperatura,
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
                    update(SensorTFModel)
                    .where(SensorTFModel.id_project == sensor_data.id_project)
                    .values(
                        distancia_cm=sensor_data.distancia_cm,
                        distancia_m=sensor_data.distancia_m,
                        fuerza_senal=sensor_data.fuerza_senal,
                        temperatura=sensor_data.temperatura,
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
            stmt = delete(SensorTFModel).where(SensorTFModel.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        # Si hay internet, eliminar también de remoto
        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorTFModel).where(SensorTFModel.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorTFModel).where(SensorTFModel.id_project == project_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_project_id(self, project_id: int, online: bool) -> SensorTFLuna | None:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(SensorTFModel).where(SensorTFModel.id_project == project_id)
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record:
                return SensorTFLuna(**record.as_dict())
            return None