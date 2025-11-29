# HCSR04/infraestructure/repositories/hc_repo_dual.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from HCSR04.domain.repositories.hc_repository import HCSensorRepository
from HCSR04.domain.entities.hc_sensor import HCSensorData
from HCSR04.infraestructure.repositories.schemas_sqlalchemy import SensorHCModel
from typing import List
import asyncio
import logging
from core.concurrency import DB_SEMAPHORE_LOCAL, DB_SEMAPHORE_REMOTE, DB_QUERY_TIMEOUT

logger = logging.getLogger(__name__)

class DualHCSensorRepository(HCSensorRepository):
    def __init__(self, session_local_factory, session_remote_factory):
        self.local_factory = session_local_factory
        self.remote_factory = session_remote_factory
    
    def _get_semaphore(self, online: bool):
        """Retorna el semáforo apropiado según el tipo de BD."""
        return DB_SEMAPHORE_REMOTE if online else DB_SEMAPHORE_LOCAL

    async def save(self, sensor_data: HCSensorData, online: bool):
        data_dict = {
            "id_project": sensor_data.id_project,
            "distancia_cm": sensor_data.distancia_cm,
            "distancia_m": sensor_data.distancia_m,
            "tiempo_vuelo_us": sensor_data.tiempo_vuelo_us,
            "event": sensor_data.event,
            "timestamp": sensor_data.timestamp,
            "synced": False  # Siempre false hasta confirmar remoto
        }
        
        # Siempre guardar localmente primero
        local_model = None
        async with self.local_factory() as session_local:
            try:
                local_model = SensorHCModel(**data_dict)
                session_local.add(local_model)
                await session_local.commit()
                try:
                    await session_local.refresh(local_model)
                except Exception:
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
                        remote_data = data_dict.copy()
                        remote_data["synced"] = True
                        remote_model = SensorHCModel(**remote_data)
                        session_remote.add(remote_model)
                        await session_remote.commit()

                        # Si el remoto tuvo éxito, actualizar el registro local
                        if local_model and local_model.id:
                            try:
                                async with self.local_factory() as session_local_upd:
                                    stmt = (update(SensorHCModel)
                                            .where(SensorHCModel.id == local_model.id)
                                            .values(synced=True))
                                    await session_local_upd.execute(stmt)
                                    await session_local_upd.commit()
                            except Exception:
                                logger.exception("HC-SR04: No se pudo marcar el registro local como synced")
                        break
                except Exception as e:
                    logger.warning("HC-SR04: Intento %s fallo al guardar en remoto: %s", attempt + 1, e)
                    if attempt < attempts - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                        continue
                    else:
                        # No forzamos un error en la API: dejamos el registro local como no sincronizado
                        logger.error("HC-SR04: No se pudo guardar en la DB remota tras %s intentos: %s", attempts, e)
                        return

    async def update_all_by_project(self, project_id: int, sensor_data: HCSensorData, online: bool):
        await self.delete_all_by_project(project_id, online)
        
        sensor_data.id_project = project_id
        await self.save(sensor_data, online)

    async def delete_all_by_project(self, project_id: int, online: bool):
        async with self.local_factory() as session_local:
            stmt = delete(SensorHCModel).where(SensorHCModel.id_project == project_id)
            await session_local.execute(stmt)
            await session_local.commit()

        if online:
            async with self.remote_factory() as session_remote:
                stmt = delete(SensorHCModel).where(SensorHCModel.id_project == project_id)
                await session_remote.execute(stmt)
                await session_remote.commit()

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = select(SensorHCModel).where(SensorHCModel.id_project == project_id).limit(1)
                        result = await session.execute(stmt)
                        return result.scalar_one_or_none() is not None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en exists_by_project HC proyecto {project_id}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False
        except Exception as e:
            logger.error(f"Error en exists_by_project HC: {e}")
            if online:
                return await self.exists_by_project(project_id, online=False)
            return False

    async def get_all_by_project_id(self, project_id: int, online: bool) -> List[HCSensorData]:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = (
                            select(SensorHCModel)
                            .where(SensorHCModel.id_project == project_id)
                            .order_by(desc(SensorHCModel.timestamp))
                        )
                        result = await session.execute(stmt)
                        records = result.scalars().all()
                        
                        return [HCSensorData(**record.as_dict()) for record in records]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_all_by_project_id HC proyecto {project_id}")
            if online:
                return await self.get_all_by_project_id(project_id, online=False)
            return []
        except Exception as e:
            logger.error(f"Error en get_all_by_project_id HC: {e}")
            if online:
                return await self.get_all_by_project_id(project_id, online=False)
            return []

    async def get_latest_by_project_id(self, project_id: int, online: bool) -> HCSensorData | None:
        factory = self.remote_factory if online else self.local_factory
        semaphore = self._get_semaphore(online)
        
        try:
            async with asyncio.timeout(DB_QUERY_TIMEOUT):
                async with semaphore:
                    async with factory() as session:
                        stmt = (
                            select(SensorHCModel)
                            .where(SensorHCModel.id_project == project_id)
                            .order_by(desc(SensorHCModel.timestamp))
                            .limit(1)
                        )
                        result = await session.execute(stmt)
                        record = result.scalar_one_or_none()
                        
                        if record:
                            return HCSensorData(**record.as_dict())
                        return None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en get_latest_by_project_id HC proyecto {project_id}")
            if online:
                return await self.get_latest_by_project_id(project_id, online=False)
            return None
        except Exception as e:
            logger.error(f"Error en get_latest_by_project_id HC: {e}")
            if online:
                return await self.get_latest_by_project_id(project_id, online=False)
            return None