# main.py
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from core.cors import setup_cors
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data
from IMX477.infraestructure.sync.sync_service import sync_imx_pending_data
from MPU6050.infraestructure.sync.sync_service import sync_mpu_pending_data
# from HCSR04.infraestructure.sync.sync_service import sync_hc_pending_data

from TFLuna.infraestructure.dependencies import init_tf_dependencies, is_connected
from IMX477.infraestructure.dependencies import init_imx_dependencies
from MPU6050.infraestructure.dependencies import init_mpu_dependencies
# from HCSR04.infraestructure.dependencies import init_hc_dependencies

from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from IMX477.infraestructure.routes.streaming_routes import router as streaming_router  # Router de streaming actualizado
from MPU6050.infraestructure.routes.routes_mpu import router as mpu_router
# from HCSR04.infraestructure.routes.routes_hc import router as hc_router

from TFLuna.infraestructure.repositories.schemas_sqlalchemy import Base as TFBase
from IMX477.infraestructure.repositories.schemas_sqlalchemy import Base as IMXBase
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import Base as MPUBase
# from HCSR04.infraestructure.repositories.schemas_sqlalchemy import Base as HCBase

local_session = get_local_engine()
remote_session = get_remote_engine()
rabbitmq_config = get_rabbitmq_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    BLE_ADDRESS = "00:11:22:33:44:55" 
    BLE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  

    print("📺 Streaming disponible en:")
    print("   - http://raspberrypi.local:8000/imx477/streaming/video")

    # Iniciar dependencias
    init_tf_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_imx_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_mpu_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected)
    # init_hc_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected, BLE_ADDRESS, BLE_CHAR_UUID)

    # Crear tablas
    async def create_tables(engine: AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(TFBase.metadata.create_all)
            await conn.run_sync(IMXBase.metadata.create_all)
            await conn.run_sync(MPUBase.metadata.create_all)
            # await conn.run_sync(HCBase.metadata.create_all)

    await create_tables(local_session.kw["bind"])
    if await is_connected():
        await create_tables(remote_session.kw["bind"])
    else:
        print("🔌 Sin conexión: se omitió la creación de tablas remotas")

    # Tarea de lectura TF
    '''async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=False)
                print("📡 TF-Luna:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                traceback.print_exc()
            await asyncio.sleep(1)'''

    # Tarea de lectura HC-SR04 BLE
    # async def hc_task():
    #     while True:
    #         try:
    #             controller = app.state.hc_controller
    #             data = await controller.get_hc_data(event=True)
    #             print("🔵 HC-SR04 BLE:", data.dict() if data else "Sin datos")
    #         except Exception as e:
    #             import traceback
    #             traceback.print_exc()
    #         await asyncio.sleep(1)  

    # Tareas de sincronización
    async def sync_tf():
        while True:
            try:
                await sync_tf_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)  # Sincronizar cada 30 segundos
            except Exception as e:
                print(f"❌ Error en sync TF: {e}")
                await asyncio.sleep(60)  # Esperar más tiempo si hay error

    async def sync_imx():
        while True:
            try:
                await sync_imx_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync IMX: {e}")
                await asyncio.sleep(60)

    async def sync_mpu():
        while True:
            try:
                await sync_mpu_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync MPU: {e}")
                await asyncio.sleep(60)

    # async def sync_hc():
    #     while True:
    #         try:
    #             await sync_hc_pending_data(local_session, remote_session, is_connected)
    #             await asyncio.sleep(30)
    #         except Exception as e:
    #             print(f"❌ Error en sync HC: {e}")
    #             await asyncio.sleep(60)

    # Iniciar tareas en segundo plano
    #asyncio.create_task(tf_task())
    # asyncio.create_task(hc_task())
    asyncio.create_task(sync_tf())
    asyncio.create_task(sync_imx())
    asyncio.create_task(sync_mpu())
    # asyncio.create_task(sync_hc())

    print("✅ Todas las tareas iniciadas correctamente")
    print("📷 Streaming de IMX477 listo para usar")
    yield

    print("🛑 Cerrando aplicación...")

app = FastAPI(
    title="Raspberry Pi Sensor API",
    description="API para sensores IMX477, TF-Luna, MPU6050 con streaming de video en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors(app)

# Configuración CORS mejorada para streaming
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://raspberrypi.local:3000",   # React en Raspberry Pi
        "http://raspberrypi.local:5173",   # Vite en Raspberry Pi
        "http://raspberrypi.local",        # Raspberry Pi general
        "http://192.168.*",                # Red local (patrón)
        "http://10.*",                     # Red local (patrón)
        "http://172.16.*",                 # Red local (patrón)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Incluir todos los routers
app.include_router(tf_router, tags=["TF-Luna"])
app.include_router(imx_router, tags=["IMX477"])
app.include_router(streaming_router, tags=["Streaming"])  # Router de streaming integrado
app.include_router(mpu_router, tags=["MPU6050"])
# app.include_router(hc_router, tags=["HC-SR04"])

# Endpoint de health check actualizado
@app.get("/")
async def root():
    return {
        "message": "Raspberry Pi Sensor API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "tf_luna": "/tf/",
            "imx477": "/imx477/",
            "streaming": {
                "start": "/imx477/streaming/start",
                "stop": "/imx477/streaming/stop",
                "video": "/imx477/streaming/video",
                "status": "/imx477/streaming/status"
            },
            "mpu6050": "/mpu6050/",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    # Importar aquí para evitar dependencias circulares
    from IMX477.infraestructure.streaming.streamer import Streamer
    
    # Crear instancia temporal para check de estado
    temp_streamer = Streamer()
    streaming_status = temp_streamer.get_status()
    
    return {
        "status": "healthy",
        "timestamp": "2025-01-15T12:00:00Z",
        "services": {
            "database": "connected" if await is_connected() else "local_only",
            "sensors": "active",
            "streaming": {
                "available": True,
                "active": streaming_status["active"],
                "fps": streaming_status["fps"]
            }
        }
    }

if __name__ == "__main__":
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",
        port=8000, 
        reload=True,
        reload_dirs=["./"],
        log_level="info",
        access_log=True
    )