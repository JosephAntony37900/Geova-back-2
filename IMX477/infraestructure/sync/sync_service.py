# IMX477/infraestructure/sync/sync_service.py
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
                            # Crear nuevo objeto sin el id para evitar conflictos
                            doc_dict = doc.as_dict()
                            doc_dict.pop('id', None)  # Remover id si existe
                            remote_model = SensorIMX477Model(**doc_dict)
                            remote.add(remote_model)
                            await remote.commit()

                        # Actualizar estado en local usando el ID específico
                        stmt_update = (
                            update(SensorIMX477Model)
                            .where(SensorIMX477Model.id == doc.id)  # Usar ID específico
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        print(f"✅ IMX Sincronizado registro ID: {doc.id}, Proyecto: {doc.id_project}")
                        
                    except Exception as e:
                        print(f"❌ Error al sincronizar IMX registro {doc.id}: {e}")
        else:
            print("🔌 Sin conexión (IMX): solo local.")
        await asyncio.sleep(10)