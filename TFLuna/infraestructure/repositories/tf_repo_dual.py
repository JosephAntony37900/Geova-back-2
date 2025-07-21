#TFLuna/infraestructure/repositories/tf_repo_dual.py
from odmantic import AIOEngine
from TFLuna.domain.entities.sensor_tf import SensorTFLuna
from TFLuna.domain.repositories.tf_repository import TFLunaRepository
from TFLuna.infraestructure.repositories.schemas import SensorTF as SensorTFModel

class TFLunaDualRepository(TFLunaRepository):
    def __init__(self, local_engine: AIOEngine, remote_engine: AIOEngine):
        self.local_engine = local_engine
        self.remote_engine = remote_engine
        
        # ✅ VERIFICAR QUE SON ENGINES DIFERENTES
        print("🏠 Local engine configurado:", self.local_engine)
        print("☁️  Remote engine configurado:", self.remote_engine)
        print("¿Son diferentes?", self.local_engine != self.remote_engine)

    async def save(self, sensor_data: SensorTFLuna, online: bool):
        model = SensorTFModel(**sensor_data.dict(), synced=False)
        
        # ✅ SIEMPRE GUARDAR EN LOCAL PRIMERO
        try:
            await self.local_engine.save(model)
            print("💾 Guardado en BASE DE DATOS LOCAL")
        except Exception as e:
            print(f"❌ Error al guardar en local: {e}")
            raise
        
        # ✅ INTENTAR GUARDAR EN REMOTO SI HAY CONEXIÓN
        if online:
            try:
                await self.remote_engine.save(model)
                model.synced = True
                await self.local_engine.save(model)  # Actualizar flag de sincronizado
                print("☁️  Guardado en BASE DE DATOS REMOTA")
            except Exception as e:
                print(f"❌ Error al guardar en remoto: {e}")
                # No lanzar excepción - local ya está guardado
        else:
            print("📡 Sin internet, solo guardado local")

    async def exists_by_project(self, project_id: int, online: bool) -> bool:
        # ✅ VERIFICAR EN REMOTO PRIMERO SI HAY CONEXIÓN
        if online:
            try:
                doc = await self.remote_engine.find_one(
                    SensorTFModel, 
                    SensorTFModel.id_project == project_id
                )
                if doc is not None:
                    print(f"✅ Proyecto {project_id} encontrado en BD REMOTA")
                    return True
            except Exception as e:
                print(f"❌ Error consultando BD remota: {e}")
        
        # ✅ VERIFICAR EN LOCAL COMO FALLBACK
        try:
            doc = await self.local_engine.find_one(
                SensorTFModel, 
                SensorTFModel.id_project == project_id
            )
            if doc is not None:
                print(f"✅ Proyecto {project_id} encontrado en BD LOCAL")
                return True
        except Exception as e:
            print(f"❌ Error consultando BD local: {e}")
        
        print(f"❌ Proyecto {project_id} NO encontrado en ninguna BD")
        return False

    async def get_by_project_id(self, project_id: int, online: bool) -> SensorTFLuna | None:
        # ✅ BUSCAR EN REMOTO PRIMERO SI HAY CONEXIÓN
        if online:
            try:
                doc = await self.remote_engine.find_one(
                    SensorTFModel, 
                    SensorTFModel.id_project == project_id
                )
                if doc:
                    print(f"📥 Datos del proyecto {project_id} obtenidos de BD REMOTA")
                    return SensorTFLuna(**doc.dict())
            except Exception as e:
                print(f"❌ Error obteniendo de BD remota: {e}")
        
        # ✅ BUSCAR EN LOCAL COMO FALLBACK
        try:
            doc = await self.local_engine.find_one(
                SensorTFModel, 
                SensorTFModel.id_project == project_id
            )
            if doc:
                print(f"📥 Datos del proyecto {project_id} obtenidos de BD LOCAL")
                return SensorTFLuna(**doc.dict())
        except Exception as e:
            print(f"❌ Error obteniendo de BD local: {e}")
        
        print(f"❌ Proyecto {project_id} no encontrado en ninguna BD")
        return None
