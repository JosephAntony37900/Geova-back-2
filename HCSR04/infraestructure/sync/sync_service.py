# HCSR04/infraestructure/sync/sync_service.py
from sqlalchemy import select, update
from HCSR04.infraestructure.repositories.schemas_sqlalchemy import SensorHCModel
import asyncio

async def sync_hc_pending_data(local_session_factory, remote_session_factory, is_connected_fn):
    try:
        if await is_connected_fn():
            async with local_session_factory() as local:
                stmt = select(SensorHCModel).where(SensorHCModel.synced == False)
                result = await local.execute(stmt)
                unsynced = result.scalars().all()

                print(f"🕒 HC-SR04 Pendientes: {len(unsynced)}")
                
                for record in unsynced:
                    try:
                        async with remote_session_factory() as remote:
                            record_dict = record.as_dict()
                            record_dict.pop('id', None)
                            record_dict['synced'] = True
                            
                            remote_model = SensorHCModel(**record_dict)
                            remote.add(remote_model)
                            await remote.commit()

                        stmt_update = (
                            update(SensorHCModel)
                            .where(SensorHCModel.id == record.id)
                            .values(synced=True)
                        )
                        await local.execute(stmt_update)
                        await local.commit()
                        
                        print(f"✅ HC-SR04 Sincronizado: ID {record.id}, Proyecto {record.id_project}")
                        
                    except Exception as e:
                        print(f"❌ Error al sincronizar HC-SR04 ID {record.id}: {e}")
        else:
            print("🔌 HC-SR04: Sin conexión - solo guardando localmente.")
            
    except Exception as e:
        print(f"❌ Error general en sync HC-SR04: {e}")
    
    await asyncio.sleep(5)