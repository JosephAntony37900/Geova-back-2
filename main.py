from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data
from IMX477.infraestructure.sync.sync_service import sync_imx_pending_data
from MPU6050.infraestructure.sync.sync_service import sync_mpu_pending_data
from HCSR04.infraestructure.sync.sync_service import sync_hc_pending_data

from TFLuna.infraestructure.dependencies import init_tf_dependencies, is_connected
from IMX477.infraestructure.dependencies import init_imx_dependencies
from MPU6050.infraestructure.dependencies import init_mpu_dependencies
from HCSR04.infraestructure.dependencies import init_hc_dependencies

from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from MPU6050.infraestructure.routes.routes_mpu import router as mpu_router
from HCSR04.infraestructure.routes.routes_hc import router as hc_router

from TFLuna.infraestructure.repositories.schemas_sqlalchemy import Base as TFBase
from IMX477.infraestructure.repositories.schemas_sqlalchemy import Base as IMXBase
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import Base as MPUBase
from HCSR04.infraestructure.repositories.schemas_sqlalchemy import Base as HCBase

from TFLuna.infraestructure.routes.routes_tf import router_ws_tf
from MPU6050.infraestructure.routes.routes_mpu import router_ws_mpu
from IMX477.infraestructure.routes.routes_imx import router_ws_imx
from HCSR04.infraestructure.routes.routes_hc import router_ws_hc

from TFLuna.infraestructure.ws.ws_manager import ws_manager
from MPU6050.infraestructure.ws.ws_manager import ws_manager_mpu
from IMX477.infraestructure.ws.ws_manager import ws_manager_imx
from HCSR04.infraestructure.ws.ws_manager import ws_manager_hc

local_session = get_local_engine()
remote_session = get_remote_engine()
rabbitmq_config = get_rabbitmq_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    BLE_ADDRESS = "00:11:22:33:44:55" 
    BLE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

    print("🚀 Iniciando dependencias de sensores...")

    init_tf_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_imx_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_mpu_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected)
    init_hc_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected, BLE_ADDRESS, BLE_CHAR_UUID)

    async def create_tables(engine: AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(TFBase.metadata.create_all)
            await conn.run_sync(IMXBase.metadata.create_all)
            await conn.run_sync(MPUBase.metadata.create_all)
            await conn.run_sync(HCBase.metadata.create_all)

    print("🗄️ Creando tablas locales...")
    await create_tables(local_session.kw["bind"])

    if await is_connected():
        print("🌐 Conexión detectada - Creando tablas remotas...")
        await create_tables(remote_session.kw["bind"])
    else:
        print("🔌 Sin conexión: se omitió la creación de tablas remotas")

    async def tf_task():
        print("🎯 Iniciando tarea TF-Luna...")
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=True)
                print("📡 TF-Luna:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager.send_data(data.dict())
            except Exception:
                import traceback
                print("❌ Error en TF-Luna:")
                traceback.print_exc()
            await asyncio.sleep(1)

    async def imx_task():
        print("📷 Iniciando tarea IMX477...")
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.imx_controller
                data = await controller.get_imx_data(event=True)
                print("📷 IMX477:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager_imx.send_data(data.dict())
            except Exception:
                import traceback
                print("❌ Error en IMX477:")
                traceback.print_exc()
            await asyncio.sleep(3)

    async def mpu_task():
        print("🌀 Iniciando tarea MPU6050...")
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.mpu_controller
                data = await controller.get_mpu_data(event=True)
                print("🌀 MPU6050:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager_mpu.send_data(data.dict())
            except Exception:
                import traceback
                print("❌ Error en MPU6050:")
                traceback.print_exc()
            await asyncio.sleep(1)

    async def hc_task():
        print("🔵 Iniciando tarea HC-SR04 BLE...")
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.hc_controller
                data = await controller.get_hc_data(event=True)
                print("🔵 HC-SR04 BLE:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager_hc.send_data(data.dict())
            except Exception:
                import traceback
                print("❌ Error en HC-SR04:")
                traceback.print_exc()
            await asyncio.sleep(2)

    async def sync_tf():
        print("🔄 Iniciando sincronización TF-Luna...")
        while True:
            try:
                if await is_connected():
                    await sync_tf_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync TF-Luna: {e}")
                await asyncio.sleep(30)

    async def sync_imx():
        print("🔄 Iniciando sincronización IMX477...")
        while True:
            try:
                if await is_connected():
                    await sync_imx_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync IMX477: {e}")
                await asyncio.sleep(30)

    async def sync_mpu():
        print("🔄 Iniciando sincronización MPU6050...")
        while True:
            try:
                if await is_connected():
                    await sync_mpu_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync MPU6050: {e}")
                await asyncio.sleep(30)

    async def sync_hc():
        print("🔄 Iniciando sincronización HC-SR04...")
        while True:
            try:
                if await is_connected():
                    await sync_hc_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Error en sync HC-SR04: {e}")
                await asyncio.sleep(30)

    print("📡 Creando tareas de sensores...")
    asyncio.create_task(tf_task())
    asyncio.create_task(imx_task())
    asyncio.create_task(mpu_task())
    asyncio.create_task(hc_task())

    print("🔄 Creando tareas de sincronización...")
    asyncio.create_task(sync_tf())
    asyncio.create_task(sync_imx())
    asyncio.create_task(sync_mpu())
    asyncio.create_task(sync_hc())

    print("🔧 Aplicación iniciada en MODO REAL")
    print("✅ Todas las tareas iniciadas correctamente")

    yield

app = FastAPI(lifespan=lifespan)

app.include_router(router_ws_tf)
app.include_router(router_ws_mpu)
app.include_router(router_ws_imx)
app.include_router(router_ws_hc)

app.include_router(tf_router)
app.include_router(imx_router)
app.include_router(mpu_router)
app.include_router(hc_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
#ok 2?