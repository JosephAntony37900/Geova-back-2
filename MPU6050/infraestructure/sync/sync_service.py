import asyncio
from MPU6050.infraestructure.repositories.schemas import SensorMPUDocument
from core.connectivity import is_connected

async def sync_mpu_data(local_engine, remote_engine):
    while True:
        if is_connected():
            unsynced = await local_engine.find(SensorMPUDocument, SensorMPUDocument.synced == False)
            for doc in unsynced:
                try:
                    await remote_engine.save(doc)
                    doc.synced = True
                    await local_engine.save(doc)
                    print(f"MPU sincronizado: {doc.id}")
                except Exception as e:
                    print(f"Error al sincronizar MPU: {e}")
        else:
            print("🔌 Sin conexión, MPU solo local.")
        await asyncio.sleep(10)
