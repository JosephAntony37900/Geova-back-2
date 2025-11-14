# TFLuna/infraestructure/repositories/tf_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.infraestructure.repositories.schemas_sqlalchemy import SensorTFModel
from datetime import datetime
import uuid
from typing import List, Optional
import asyncio
import logging

class DualTFLunaRepository(TFLunaRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory

    async def save(self, sensor_data: SensorTFLuna, online: bool):
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)
        # Siempre guardar localmente primero. Marcar como no sincronizado
        # hasta que el guardado remoto confirme la persistencia.
        async with self.local_factory() as session_local:
            try:
                local_model = SensorTFModel(**data_dict, synced=False)
                session_local.add(local_model)
                await session_local.commit()
                # refrescar para obtener el id si es necesario
                try:
                    await session_local.refresh(local_model)
                except Exception:
                    # refresh es opcional, no bloquear si falla
                    pass
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            # Intentar guardar en la base remota con reintentos y backoff.
            attempts = 3
            for attempt in range(attempts):
                try:
                    async with self.remote_factory() as session_remote:
                        remote_model = SensorTFModel(**data_dict, synced=True)
                        session_remote.add(remote_model)
                        await session_remote.commit()

                        # Si el remoto tuvo éxito, actualizar el registro local
                        try:
                            async with self.local_factory() as session_local_upd:
                                stmt = (update(SensorTFModel)
                                        .where(SensorTFModel.id == local_model.id)
                                        .values(synced=True))
                                await session_local_upd.execute(stmt)
                                await session_local_upd.commit()
                        except Exception:
                            # Si no podemos marcarlo como synced localmente, lo dejamos
                            logging.exception("No se pudo marcar el registro local como synced")
                        break
                except Exception as e:
                    # rollback si el session_remote está abierto (context manager se encarga normalmente)
                    logging.warning("Intento %s fallo al guardar en remoto: %s", attempt + 1, e)
                    if attempt < attempts - 1:
                        # backoff exponencial pequeño
                        await asyncio.sleep(0.5 * (2 ** attempt))
                        continue
                    else:
                        # No forzamos un error en la API: dejamos el registro local como no sincronizado
                        logging.error("No se pudo guardar en la DB remota tras %s intentos: %s", attempts, e)
                        return

    async def update(self, sensor_data: SensorTFLuna, online: bool):
        if sensor_data.id is None:
            raise ValueError("Falta el ID para actualizar el registro")

        update_values = {
            'id_project': sensor_data.id_project,
            'distancia_cm': sensor_data.distancia_cm,
            'distancia_m': sensor_data.distancia_m,
            'fuerza_senal': sensor_data.fuerza_senal,
            'temperatura': sensor_data.temperatura,
            'event': sensor_data.event,
            'timestamp': sensor_data.timestamp,
            'is_dual_measurement': sensor_data.is_dual_measurement,
            'measurement_count': sensor_data.measurement_count,
            'total_distance_cm': sensor_data.total_distance_cm,
            'total_distance_m': sensor_data.total_distance_m,
            'synced': online
        }

        async with self.local_factory() as session_local:
            try:
                stmt = update(SensorTFModel).where(
                    SensorTFModel.id == sensor_data.id
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
                    stmt = update(SensorTFModel).where(
                        SensorTFModel.id == sensor_data.id
                    ).values(**remote_values)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorTFModel).where(SensorTFModel.id_project == project_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorTFModel).where(SensorTFModel.id_project == project_id)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete_by_id(self, record_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorTFModel).where(SensorTFModel.id == record_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorTFModel).where(SensorTFModel.id == record_id)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = select(func.count()).select_from(SensorTFModel).where(
                SensorTFModel.id_project == project_id
            )
            result = await session.execute(stmt)
            count = result.scalar()
            return count >= 4

    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            stmt = (
                select(SensorTFModel)
                .where(SensorTFModel.id_project == project_id)
                .order_by(SensorTFModel.timestamp.desc())
                .limit(4)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [SensorTFLuna(**r.as_dict()) for r in records]

    async def get_dual_measurement(self, project_id: int, online: bool) -> Optional[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = (
                    select(SensorTFModel)
                    .where(
                        SensorTFModel.id_project == project_id,
                        SensorTFModel.is_dual_measurement == True
                    )
                    .order_by(SensorTFModel.timestamp.desc())
                    .limit(1)
                )
                result = await session.execute(stmt)
                record = result.scalars().first()
                return SensorTFLuna(**record.as_dict()) if record else None
            except Exception as e:
                await session.rollback()
                raise e

    async def exists_dual_measurement(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = select(func.count()).select_from(SensorTFModel).where(
                    SensorTFModel.id_project == project_id,
                    SensorTFModel.is_dual_measurement == True
                )
                result = await session.execute(stmt)
                count = result.scalar()
                return count > 0
            except Exception as e:
                await session.rollback()
                raise e
                
    async def has_any_record(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = select(func.count()).select_from(SensorTFModel).where(
                    SensorTFModel.id_project == project_id
                )
                result = await session.execute(stmt)
                count = result.scalar()
                return count > 0
            except Exception as e:
                await session.rollback()
                raise e
                
    async def get_by_id(self, record_id: int, online: bool) -> Optional[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        async with factory() as session:
            try:
                stmt = select(SensorTFModel).where(SensorTFModel.id == record_id)
                result = await session.execute(stmt)
                record = result.scalars().first()
                return SensorTFLuna(**record.as_dict()) if record else None
            except Exception as e:
                await session.rollback()
                raise e