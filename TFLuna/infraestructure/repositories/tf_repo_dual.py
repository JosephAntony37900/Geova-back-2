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
from core.concurrency import DB_SEMAPHORE_LOCAL, DB_SEMAPHORE_REMOTE, DB_QUERY_TIMEOUT

logger = logging.getLogger(__name__)

class DualTFLunaRepository(TFLunaRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory
    
    def _get_semaphore(self, online: bool):
        """Retorna el semáforo apropiado según el tipo de BD."""
        return DB_SEMAPHORE_REMOTE if online else DB_SEMAPHORE_LOCAL

    async def save(self, sensor_data: SensorTFLuna, online: bool):
        """Guarda localmente (rápido). La sincronización remota la hace sync_service en background."""
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)
        
        # Solo guardar localmente - el sync_service se encarga del remoto
        async with self.local_factory() as session_local:
            try:
                local_model = SensorTFModel(**data_dict, synced=False)
                session_local.add(local_model)
                await session_local.commit()
                logger.debug("TFLuna: Guardado local exitoso, pendiente de sync")
            except Exception as e:
                await session_local.rollback()
                raise e

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
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(func.count()).select_from(SensorTFModel).where(
                            SensorTFModel.id_project == project_id
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count >= 4
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en exists_by_project TFLuna proyecto {project_id}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en exists_by_project TFLuna: {e}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False

    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
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
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_by_project_id TFLuna proyecto {project_id}")
            if online:
                return await self.get_by_project_id(project_id, online=False)
            return []
        except Exception as e:
            logger.error(f"Error en get_by_project_id TFLuna: {e}")
            if online:
                return await self.get_by_project_id(project_id, online=False)
            return []

    async def get_dual_measurement(self, project_id: int, online: bool) -> Optional[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
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
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_dual_measurement TFLuna proyecto {project_id}")
            if online:
                return await self.get_dual_measurement(project_id, online=False)
            return None
        except Exception as e:
            logger.error(f"Error en get_dual_measurement TFLuna: {e}")
            if online:
                return await self.get_dual_measurement(project_id, online=False)
            return None

    async def exists_dual_measurement(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(func.count()).select_from(SensorTFModel).where(
                            SensorTFModel.id_project == project_id,
                            SensorTFModel.is_dual_measurement == True
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count > 0
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en exists_dual_measurement TFLuna proyecto {project_id}")
            if online:
                return await self.exists_dual_measurement(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en exists_dual_measurement TFLuna: {e}")
            if online:
                return await self.exists_dual_measurement(project_id, online=False)
            return False
                
    async def has_any_record(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(func.count()).select_from(SensorTFModel).where(
                            SensorTFModel.id_project == project_id
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count > 0
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en has_any_record TFLuna proyecto {project_id}")
            if online:
                return await self.has_any_record(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en has_any_record TFLuna: {e}")
            if online:
                return await self.has_any_record(project_id, online=False)
            return False
                
    async def get_by_id(self, record_id: int, online: bool) -> Optional[SensorTFLuna]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(SensorTFModel).where(SensorTFModel.id == record_id)
                        result = await session.execute(stmt)
                        record = result.scalars().first()
                        return SensorTFLuna(**record.as_dict()) if record else None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_by_id TFLuna id {record_id}")
            if online:
                return await self.get_by_id(record_id, online=False)
            return None
        except Exception as e:
            logger.error(f"Error en get_by_id TFLuna: {e}")
            if online:
                return await self.get_by_id(record_id, online=False)
            return None