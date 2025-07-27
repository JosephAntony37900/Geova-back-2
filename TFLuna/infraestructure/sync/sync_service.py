# TFLuna/infraestructure/sync/sync_service.py
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
                            # Crear nuevo objeto sin el id para evitar conflictos
                            doc_dict = doc.as_dict()
                            doc_dict.pop('id', None)  # ✅ Remover id para remote
                            remote_model = SensorTFModel(**doc_dict)
                            remote.add(remote_model)
                            await remote.commit()

                        # ✅ CORRECCIÓN: Actualizar por ID específico, no por project_id
                        stmt_update = (
                            update(SensorTFModel)
                            .where(SensorTFModel.id == doc.id)  # ✅ ID específico
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        print(f"✅ Sincronizado registro ID: {doc.id}, Proyecto: {doc.id_project}")
                        
                    except Exception as e:
                        print(f"❌ Error al sincronizar registro {doc.id}: {e}")
        else:
            print("🔌 Sin conexión: solo guardando localmente.")
        await asyncio.sleep(10)