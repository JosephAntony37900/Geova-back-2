from core.config import get_dual_engines
from core.connectivity import is_connected

async def check_databases_health():
    """Verificar que ambas bases de datos estén funcionando"""
    db_engines = get_dual_engines()
    
    results = {
        "local": False,
        "remote": False,
        "connectivity": is_connected()
    }
    
    # Verificar BD Local
    try:
        # Hacer un ping simple
        await db_engines.local.get_collection("health_check").count_documents({})
        results["local"] = True
        print("✅ Base de datos LOCAL funcionando")
    except Exception as e:
        print(f"❌ Error en base de datos LOCAL: {e}")
    
    # Verificar BD Remota
    if results["connectivity"]:
        try:
            await db_engines.remote.get_collection("health_check").count_documents({})
            results["remote"] = True
            print("✅ Base de datos REMOTA funcionando")
        except Exception as e:
            print(f"❌ Error en base de datos REMOTA: {e}")
    else:
        print("📡 Sin conexión - no verificando BD remota")
    
    return results