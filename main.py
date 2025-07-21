# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data
from IMX477.infraestructure.sync.sync_service import sync_imx_pending_data
from MPU6050.infraestructure.sync.sync_service import sync_mpu_pending_data

from TFLuna.infraestructure.dependencies import init_tf_dependencies, is_connected
from IMX477.infraestructure.dependencies import init_imx_dependencies
from MPU6050.infraestructure.dependencies import init_mpu_dependencies

from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from MPU6050.infraestructure.routes.routes_mpu import router as mpu_router

from TFLuna.infraestructure.repositories.schemas_sqlalchemy import Base as TFBase
from IMX477.infraestructure.repositories.schemas_sqlalchemy import Base as IMXBase
from MPU6050.infraestructure.repositories.schemas_sqlalchemy import Base as MPUBase

local_session = get_local_engine()
remote_session = get_remote_engine()
rabbitmq_config = get_rabbitmq_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar dependencias
    init_tf_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_imx_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_mpu_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected)

    # Crear tablas
    async def create_tables(engine: AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(TFBase.metadata.create_all)
            await conn.run_sync(IMXBase.metadata.create_all)
            await conn.run_sync(MPUBase.metadata.create_all)

    await create_tables(local_session.kw["bind"])
    if await is_connected():
        await create_tables(remote_session.kw["bind"])
    else:
        print("🔌 Sin conexión: se omitió la creación de tablas remotas")

    # Tarea de lectura TF
    async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=True)
                print("📡 TF-Luna:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                traceback.print_exc()
            await asyncio.sleep(1)

    # Tarea de lectura MPU eliminada - no necesaria

    # Tareas de sincronización
    async def sync_tf():
        await sync_tf_pending_data(local_session, remote_session, is_connected)

    async def sync_imx():
        await sync_imx_pending_data(local_session, remote_session, is_connected)

    async def sync_mpu():
        await sync_mpu_pending_data(local_session, remote_session, is_connected)

    asyncio.create_task(tf_task())
    # asyncio.create_task(mpu_task())  # Eliminado - no necesario
    asyncio.create_task(sync_tf())
    asyncio.create_task(sync_imx())
    asyncio.create_task(sync_mpu())

    yield

app = FastAPI(lifespan=lifespan)

app.include_router(tf_router)
app.include_router(imx_router)
app.include_router(mpu_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)