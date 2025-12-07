# IMX477/infraestructure/repositories/imx_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
from IMX477.domain.repositories.imx_repository import IMXRepository
from IMX477.domain.entities.sensor_imx import SensorIMX477
from IMX477.infraestructure.repositories.schemas_sqlalchemy import SensorIMX477Model
from datetime import datetime
from typing import List, Optional
import asyncio
import logging
from core.concurrency import DB_SEMAPHORE_LOCAL, DB_SEMAPHORE_REMOTE, DB_QUERY_TIMEOUT

logger = logging.getLogger(__name__)

class DualIMXRepository(IMXRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory
    
    def _get_semaphore(self, online: bool):
        """Retorna el semáforo apropiado según el tipo de BD."""
        return DB_SEMAPHORE_REMOTE if online else DB_SEMAPHORE_LOCAL

    async def save(self, sensor_data: SensorIMX477, online: bool):
        """Guarda localmente (rápido). La sincronización remota la hace sync_service en background."""
        data_dict = sensor_data.dict()
        data_dict.pop('id', None)
        
        # Solo guardar localmente - el sync_service se encarga del remoto
        async with self.local_factory() as session_local:
            try:
                local_model = SensorIMX477Model(**data_dict, synced=False)
                session_local.add(local_model)
                await session_local.commit()
                logger.debug("IMX477: Guardado local exitoso, pendiente de sync")
            except Exception as e:
                await session_local.rollback()
                raise e

    async def update(self, sensor_data: SensorIMX477, online: bool):
        if sensor_data.id is None:
            raise ValueError("Falta el ID para actualizar el registro")

        update_values = {
            'id_project': sensor_data.id_project,
            'resolution': sensor_data.resolution,
            'luminosidad_promedio': sensor_data.luminosidad_promedio,
            'nitidez_score': sensor_data.nitidez_score,
            'laser_detectado': sensor_data.laser_detectado,
            'calidad_frame': sensor_data.calidad_frame,
            'probabilidad_confiabilidad': sensor_data.probabilidad_confiabilidad,
            'event': sensor_data.event,
            'timestamp': sensor_data.timestamp,
            'is_dual_measurement': sensor_data.is_dual_measurement,
            'measurement_count': sensor_data.measurement_count,
            'avg_luminosidad': sensor_data.avg_luminosidad,
            'avg_nitidez': sensor_data.avg_nitidez,
            'avg_calidad': sensor_data.avg_calidad,
            'avg_probabilidad': sensor_data.avg_probabilidad,
            'synced': online
        }

        async with self.local_factory() as session_local:
            try:
                stmt = update(SensorIMX477Model).where(
                    SensorIMX477Model.id == sensor_data.id
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
                    stmt = update(SensorIMX477Model).where(
                        SensorIMX477Model.id == sensor_data.id
                    ).values(**remote_values)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id_project == project_id)
                    await session_remote.execute(stmt)
                    await session_remote.commit()
                except Exception as e:
                    await session_remote.rollback()
                    raise e

    async def delete_by_id(self, record_id: int, online: bool):
        async with self.local_factory() as session_local:
            try:
                stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id == record_id)
                await session_local.execute(stmt)
                await session_local.commit()
            except Exception as e:
                await session_local.rollback()
                raise e

        if online:
            async with self.remote_factory() as session_remote:
                try:
                    stmt = delete(SensorIMX477Model).where(SensorIMX477Model.id == record_id)
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
                        stmt = select(func.count()).select_from(SensorIMX477Model).where(
                            SensorIMX477Model.id_project == project_id
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count >= 4
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en exists_by_project IMX477 proyecto {project_id}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en exists_by_project IMX477: {e}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False

    async def get_by_project_id(self, project_id: int, online: bool) -> List[SensorIMX477]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
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
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_by_project_id IMX477 proyecto {project_id}")
            # Fallback a local si remoto falla
            if online:
                return await self.get_by_project_id(project_id, online=False)
            return []
        except Exception as e:
            logger.error(f"Error en get_by_project_id IMX477: {e}")
            if online:
                return await self.get_by_project_id(project_id, online=False)
            return []

    async def get_dual_measurement(self, project_id: int, online: bool) -> Optional[SensorIMX477]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = (
                            select(SensorIMX477Model)
                            .where(
                                SensorIMX477Model.id_project == project_id,
                                SensorIMX477Model.is_dual_measurement == True
                            )
                            .order_by(SensorIMX477Model.timestamp.desc())
                            .limit(1)
                        )
                        result = await session.execute(stmt)
                        record = result.scalars().first()
                        return SensorIMX477(**record.as_dict()) if record else None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_dual_measurement IMX477 proyecto {project_id}")
            if online:
                return await self.get_dual_measurement(project_id, online=False)
            return None
        except Exception as e:
            logger.error(f"Error en get_dual_measurement IMX477: {e}")
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
                        stmt = select(func.count()).select_from(SensorIMX477Model).where(
                            SensorIMX477Model.id_project == project_id,
                            SensorIMX477Model.is_dual_measurement == True
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count > 0
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en exists_dual_measurement IMX477 proyecto {project_id}")
            if online:
                return await self.exists_dual_measurement(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en exists_dual_measurement IMX477: {e}")
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
                        stmt = select(func.count()).select_from(SensorIMX477Model).where(
                            SensorIMX477Model.id_project == project_id
                        )
                        result = await session.execute(stmt)
                        count = result.scalar()
                        return count > 0
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en has_any_record IMX477 proyecto {project_id}")
            if online:
                return await self.has_any_record(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en has_any_record IMX477: {e}")
            if online:
                return await self.has_any_record(project_id, online=False)
            return False
                
    async def get_by_id(self, record_id: int, online: bool) -> Optional[SensorIMX477]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(SensorIMX477Model).where(SensorIMX477Model.id == record_id)
                        result = await session.execute(stmt)
                        record = result.scalars().first()
                        return SensorIMX477(**record.as_dict()) if record else None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_by_id IMX477 id {record_id}")
            if online:
                return await self.get_by_id(record_id, online=False)
            return None
        except Exception as e:
            logger.error(f"Error en get_by_id IMX477: {e}")
            if online:
                return await self.get_by_id(record_id, online=False)
            return None