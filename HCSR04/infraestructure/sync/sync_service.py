import asyncio
from HCSR04.infraestructure.repositories.schemas import SensorHCSR04
from core.connectivity import is_connected

async def sync_hc_data(local_engine, remote_engine):
    while True:
        if is_connected():
            unsynced = await local_engine.find(SensorHCSR04, SensorHCSR04.synced == False)
            for doc in unsynced:
                try:
                    await remote_engine.save(doc)
                    doc.synced = True
                    await local_engine.save(doc)
                    print(f"[HC-SR04] Sincronizado: {doc.id}")
                except Exception as e:
                    print(f"[HC-SR04] Error al sincronizar: {e}")
        else:
            print("🔌 [HC-SR04] Sin conexión: solo guardando localmente.")
        await asyncio.sleep(10)
