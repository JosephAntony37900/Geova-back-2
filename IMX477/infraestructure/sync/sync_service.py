import asyncio
from sqlalchemy import select, update
from IMX477.infraestructure.repositories.schemas_sqlalchemy import SensorIMX477Model

async def sync_imx_pending_data(local_session_factory, remote_session_factory, is_connected_fn):
    while True:
        if await is_connected_fn():
            async with local_session_factory() as local:
                stmt = select(SensorIMX477Model).where(SensorIMX477Model.synced == False)
                result = await local.execute(stmt)
                unsynced = result.scalars().all()

                print(f"🕒 Pendientes IMX: {len(unsynced)}")
                for doc in unsynced:
                    try:
                        async with remote_session_factory() as remote:
                            remote.add(SensorIMX477Model(**doc.as_dict()))
                            await remote.commit()

                        stmt_update = (
                            update(SensorIMX477Model)
                            .where(SensorIMX477Model.id_project == doc.id_project)
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        print(f"✅ IMX sincronizado: {doc.id_project}")
                    except Exception as e:
                        print(f"❌ Error al sincronizar IMX: {e}")
        else:
            print("🔌 Sin conexión (IMX): solo local.")
        await asyncio.sleep(10)
