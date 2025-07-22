# MPU6050/infraestructure/sync/sync_service.py
from sqlalchemy import select, update
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import SensorMPUModel
import asyncio

async def sync_mpu_pending_data(local_session_factory, remote_session_factory, is_connected_fn):
    while True:
        if await is_connected_fn():
            async with local_session_factory() as local:
                stmt = select(SensorMPUModel).where(SensorMPUModel.synced == False)
                result = await local.execute(stmt)
                unsynced = result.scalars().all()

                print(f"🕒 MPU Pendientes: {len(unsynced)}")
                for doc in unsynced:
                    try:
                        async with remote_session_factory() as remote:
                            remote.add(SensorMPUModel(**doc.as_dict()))
                            await remote.commit()

                        # Actualizar estado en local
                        stmt_update = (
                            update(SensorMPUModel)
                            .where(SensorMPUModel.id_project == doc.id_project)
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        print(f"MPU Sincronizado: {doc.id_project}")
                    except Exception as e:
                        print(f"Error al sincronizar MPU: {e}")
        else:
            print("🔌 Sin conexión MPU: solo guardando localmente.")
        await asyncio.sleep(10)