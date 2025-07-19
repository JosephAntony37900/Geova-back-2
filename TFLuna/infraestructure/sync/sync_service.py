import asyncio
from TFLuna.infraestructure.repositories.schemas import SensorTF
from core.connectivity import is_connected

async def sync_tf_pending_data(local_engine, remote_engine):
    while True:
        if is_connected():
            unsynced = await local_engine.find(SensorTF, SensorTF.synced == False)
            for doc in unsynced:
                try:
                    await remote_engine.save(doc)
                    doc.synced = True
                    await local_engine.save(doc)
                    print(f"Sincronizado: {doc.id}")
                except Exception as e:
                    print(f"Error al sincronizar: {e}")
        else:
            print("🔌 Sin conexión: solo guardando localmente.")
        await asyncio.sleep(10)
