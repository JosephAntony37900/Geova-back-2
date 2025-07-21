#IMX477/infraestructure/sync_service.py
import asyncio
from IMX477.infraestructure.repositories.schemas import SensorIMXDocument
from core.connectivity import is_connected

async def sync_imx_pending_data(local_engine, remote_engine):
    while True:
        if is_connected():
            unsynced = await local_engine.find(SensorIMXDocument, SensorIMXDocument.synced == False)
            for doc in unsynced:
                try:
                    await remote_engine.save(doc)
                    doc.synced = True
                    await local_engine.save(doc)
                    print(f"Sincronizado: {doc.id}")
                except Exception as e:
                    print(f"Error al sincronizar datos (MPU6050): {e}")
        else:
            print("🔌 Sin conexión: solo guardando localmente.")
        await asyncio.sleep(10)
