# IMX477/infraestructure/repositories/imx_repo_dual.py
from sqlalchemy import select, update, delete, func
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.repositories.schemas_sqlalchemy import SensorIMX477Model
from typing import List

class DualIMXRepository(IMXRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorIMX477, online: bool):
        # Crear diccionario sin el ID para que sea autoincremental
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)  # Remover id si existe
        
        async with self.local_factory() as session_local:
            local_model = SensorIMX477Model(**data_dict, synced=online)
            session_local.add(local_model)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                remote_model = SensorIMX477Model(**data_dict, synced=True)
                session_remote.add(remote_model)
                await session_remote.commit()

    async def update(self, sensor_data: SensorIMX477, online: bool):
        if sensor_data.id is None:
            raise ValueError("Falta el ID para actualizar el registro IMX")

        update_data = {
            'id_project': sensor_data.id_project,
            'resolution': sensor_data.resolution,
            'luminosidad_promedio': sensor_data.luminosidad_promedio,
            'nitidez_score': sensor_data.nitidez_score,
            'laser_detectado': sensor_data.laser_detectado,
            'calidad_frame': sensor_data.calidad_frame,
            'probabilidad_confiabilidad': sensor_data.probabilidad_confiabilidad,
            'event': sensor_data.event,
            'timestamp': sensor_data.timestamp,
            'synced': online
        }

        async with self.local_factory() as session_local:
            stmt = (
                update(SensorIMX477Model)
                .where(SensorIMX477Model.id == sensor_data.id)
                .values(**update_data)
            )
            await session_local.execute(stmt)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                update_data['synced'] = True
                stmt = (
                    update(SensorIMX477Model)
                    .where(SensorIMX477Model.id == sensor_data.id)
                    .values(**update_data)
                )
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(func.count()).select_from(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
            result = await session.execute(stmt)
            count = result.scalar()
            return count >= 4

    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorIMX477]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = (
                select(SensorIMX477Model)
                .where(SensorIMX477Model.id_project == project_id)
                .order_by(SensorIMX477Model.timestamp.desc())
                .limit(4)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [SensorIMX477(**r.as_dict()) for r in records]