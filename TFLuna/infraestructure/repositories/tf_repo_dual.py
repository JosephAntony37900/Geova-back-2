# TFLuna/infraestructure/repositories/tf_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.infraestructure.repositories.schemas_sqlalchemy import SensorTFModel
from datetime import datetime
import uuid
from typing import List

class DualTFLunaRepository(TFLunaRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorTFLuna, online: bool):
    # Crear diccionario sin el ID para que sea autoincremental
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)  # ✅ IMPORTANTE: Remover id para evitar conflictos
        
        async with self.local_factory() as session_local:
                local_model = SensorTFModel(**data_dict, synced=online)
                session_local.add(local_model)
                await session_local.commit()

        if online:
                async with self.remote_factory() as session_remote:
                        remote_model = SensorTFModel(**data_dict, synced=True)
                        session_remote.add(remote_model)
                        await session_remote.commit()

    async def update(self, sensor_data: SensorTFLuna, online: bool):
        if sensor_data.id is None:
                raise ValueError("Falta el ID para actualizar el registro")

        async with self.local_factory() as session_local:
                stmt = (
                        update(SensorTFModel)
                        .where(SensorTFModel.id == sensor_data.id)
                        .values(
                                id_project=sensor_data.id_project,
                                distancia_cm=sensor_data.distancia_cm,
                                distancia_m=sensor_data.distancia_m,
                                fuerza_senal=sensor_data.fuerza_senal,
                                temperatura=sensor_data.temperatura,
                                event=sensor_data.event,
                                timestamp=sensor_data.timestamp,
                                synced=online
                        )
                )
                await session_local.execute(stmt)
                await session_local.commit()

        if online:
                async with self.remote_factory() as session_remote:
                        stmt = (
                                update(SensorTFModel)
                                .where(SensorTFModel.id == sensor_data.id)
                                .values(
                                        id_project=sensor_data.id_project,
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
            stmt = select(func.count()).select_from(SensorTFModel).where(SensorTFModel.id_project == project_id)
            result = await session.execute(stmt)
            count = result.scalar()
            return count >= 4


    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = (
                select(SensorTFModel)
                .where(SensorTFModel.id_project == project_id)
            .order_by(SensorTFModel.timestamp.desc())  # Opcional: orden cronológico
            .limit(4)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()
        return [SensorTFLuna(**r.as_dict()) for r in records]
