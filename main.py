from fastapi import FastAPI
import uvicorn, asyncio

from core.config import get_engine, get_rabbitmq_config, get_remote_engine, get_dual_engines
from core.connectivity import is_connected
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data

# TF-Luna
from TFLuna.infraestructure.dependencies import init_tf_dependencies
from TFLuna.infraestructure.routes.routes_tf import router as tf_router

# IMX477
from IMX477.infraestructure.dependencies import init_imx_dependencies
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from IMX477.infraestructure.sync.sync_service import sync_imx_pending_data

# Graph
from Graph.infraestructure.routes.routes_graph import router as graph_router
from Graph.infraestructure.dependencies import init_graph_dependencies

# MPU6050
from MPU6050.infraestructure.dependencies import init_mpu_dependencies
from MPU6050.infraestructure.routes.routes_mpu import router as mpu_router
from MPU6050.infraestructure.sync.sync_service import sync_mpu_data

# HCSR04
from HCSR04.infraestructure.dependencies import init_hc_dependencies
from HCSR04.infraestructure.routes.routes_hc import router as hc_router
from HCSR04.infraestructure.sync.sync_service import sync_hc_data

app = FastAPI()

# ✅ NUEVA IMPLEMENTACIÓN DUAL - OBTENER AMBOS ENGINES
print("🚀 Configurando bases de datos duales...")
db_engines = get_dual_engines()
print(f"🏠 Engine LOCAL configurado: {type(db_engines.local)}")
print(f"☁️  Engine REMOTO configurado: {type(db_engines.remote)}")
print(f"✅ Engines son diferentes: {db_engines.local != db_engines.remote}")

# Configuración RabbitMQ
rabbitmq_config = get_rabbitmq_config()

# ✅ INICIALIZAR DEPENDENCIAS CON ENGINES DUALES
# Para sensores que ya soportan dual engine:
init_tf_dependencies(app, db_engines.local, db_engines.remote, rabbitmq_config, is_connected)

engine = db_engines.local
remote_engine = db_engines.remote

#init_imx_dependencies(app, engine, rabbitmq_config)
#init_graph_dependencies(app, engine)
#init_mpu_dependencies(app, engine, rabbitmq_config)
#init_hc_dependencies(app, engine, rabbitmq_config)

@app.on_event("startup")
async def start_tasks():
    print("🚀 Iniciando tareas de sensores y sincronización...")
    
    async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=True)
                print("TF-Luna leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                print("Error en TF-Luna:")
                traceback.print_exc()
            await asyncio.sleep(1)

    '''async def imx_task():
        while True:
            try:
                controller = app.state.imx_controller
                data = await controller.get_imx_data(event=False)
                print("IMX477 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                print("Error en IMX477:")
                traceback.print_exc()
            await asyncio.sleep(3)'''

    '''async def mpu_task():
        while True:
            try:
                controller = app.state.mpu_controller
                data = await controller.get_mpu_data(event=False)
                print("MPU6050 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                print("Error en MPU6050:", e)
            await asyncio.sleep(1)'''
            
    '''async def hc_task():
        while True:
            try:
                controller = app.state.hc_controller
                data = await controller.get_hc_data(event=True)
                print("HC-SR04 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                print("Error en HC-SR04:", e)
            await asyncio.sleep(2)'''

    async def sync_tf_task():
        print("🔄 Iniciando sincronización TF-Luna...")
        await sync_tf_pending_data(
            local_engine=db_engines.local,
            remote_engine=db_engines.remote
        )

    '''async def imx_sync_task():
        print("🔄 Iniciando sincronización IMX477...")
        await sync_imx_pending_data(
            local_engine=db_engines.local,
            remote_engine=db_engines.remote
        )'''
    
    '''async def mpu_sync_task():
        print("🔄 Iniciando sincronización MPU6050...")
        await sync_mpu_data(
            local_engine=db_engines.local,
            remote_engine=db_engines.remote
        )'''
    
    '''async def hc_sync_task():
        print("🔄 Iniciando sincronización HC-SR04...")
        await sync_hc_data(
            local_engine=db_engines.local,
            remote_engine=db_engines.remote
        )'''

    print("📡 Creando tareas asíncronas...")
    asyncio.create_task(tf_task())
    '''asyncio.create_task(imx_task()) 
    asyncio.create_task(mpu_task())
    asyncio.create_task(hc_task())'''
    
    # Tareas de sincronización
    asyncio.create_task(sync_tf_task())
    '''asyncio.create_task(imx_sync_task())
    asyncio.create_task(mpu_sync_task())
    asyncio.create_task(hc_sync_task())'''
    
    print("✅ Todas las tareas iniciadas correctamente")

app.include_router(tf_router)
#app.include_router(imx_router)
#app.include_router(graph_router)
#app.include_router(mpu_router)
#app.include_router(hc_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)