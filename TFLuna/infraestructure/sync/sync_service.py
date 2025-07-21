from sqlalchemy import select, update
from TFLuna.infraestructure.repositories.schemas_sqlalchemy import SensorTFModel
import asyncio

async def sync_tf_pending_data(local_session_factory, remote_session_factory, is_connected_fn):
    while True:
        if await is_connected_fn():
            async with local_session_factory() as local:
                stmt = select(SensorTFModel).where(SensorTFModel.synced == False)
                result = await local.execute(stmt)
                unsynced = result.scalars().all()

                print(f"🕒 Pendientes: {len(unsynced)}")
                for doc in unsynced:
                    try:
                        async with remote_session_factory() as remote:
                            remote.add(SensorTFModel(**doc.as_dict()))
                            await remote.commit()

                        # Actualizar estado en local
                        stmt_update = (
                            update(SensorTFModel)
                            .where(SensorTFModel.id_project == doc.id_project)
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        print(f"Sincronizado: {doc.id_project}")
                    except Exception as e:
                        print(f"Error al sincronizar: {e}")
        else:
            print("🔌 Sin conexión: solo guardando localmente.")
        await asyncio.sleep(10)