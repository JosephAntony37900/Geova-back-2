import asyncio
from core.config import get_dual_engines
from core.database_health import check_databases_health

async def test_dual_databases():
    """Script para probar que ambas bases de datos funcionan correctamente"""
    print("🔍 Iniciando test de bases de datos duales...")
    
    # 1. Obtener engines
    db_engines = get_dual_engines()
    print(f"Local engine: {db_engines.local}")
    print(f"Remote engine: {db_engines.remote}")
    print(f"¿Son diferentes?: {db_engines.local != db_engines.remote}")
    
    # 2. Verificar salud de las bases de datos
    health = await check_databases_health()
    print("Estado de salud:", health)
    
    # 3. Test básico de escritura/lectura
    from TFLuna.infraestructure.repositories.schemas import SensorTF
    from datetime import datetime
    
    # Crear documento de prueba
    test_doc = SensorTF(
        id_project=999,
        distance=123.45,
        timestamp=datetime.now(),
        synced=False
    )
    
    try:
        # Guardar en local
        await db_engines.local.save(test_doc)
        print("✅ Test guardado en BD LOCAL")
        
        # Guardar en remoto si hay conexión
        if health["connectivity"] and health["remote"]:
            await db_engines.remote.save(test_doc)
            print("✅ Test guardado en BD REMOTA")
        
        # Leer de ambas
        local_doc = await db_engines.local.find_one(SensorTF, SensorTF.id_project == 999)
        print(f"📖 Leído de LOCAL: {local_doc is not None}")
        
        if health["connectivity"] and health["remote"]:
            remote_doc = await db_engines.remote.find_one(SensorTF, SensorTF.id_project == 999)
            print(f"📖 Leído de REMOTO: {remote_doc is not None}")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
    
    print("🏁 Test completado")

if __name__ == "__main__":
        asyncio.run(test_dual_databases())