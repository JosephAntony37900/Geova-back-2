from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data
from TFLuna.infraestructure.dependencies import init_tf_dependencies, is_connected
from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from TFLuna.infraestructure.repositories.schemas_sqlalchemy import Base
from TFLuna.infraestructure.dependencies import is_connected


# Inicializamos fuera del ciclo de vida para que estén disponibles
local_session = get_local_engine()
remote_session = get_remote_engine()
rabbitmq_config = get_rabbitmq_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 👉 Configurar dependencias
    init_tf_dependencies(app, local_session, remote_session, rabbitmq_config)
    
    async def create_tables(engine: AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await create_tables(local_session.kw["bind"])
    if await is_connected():
        await create_tables(remote_session.kw["bind"])
    else:
        print("🔌 Sin conexión: se omitió la creación de tablas en PostgreSQL")


    # 🧵 Tareas de lectura y sincronización
    async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=True)
                print("TF-Luna leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                traceback.print_exc()
            await asyncio.sleep(1)

    async def sync_task():
        await sync_tf_pending_data(local_session, remote_session, is_connected)

    # 🚀 Lanzamos las tareas
    asyncio.create_task(tf_task())
    asyncio.create_task(sync_task())

    yield  # Lifespan activo

    # Aquí puedes cerrar recursos si los necesitas (por ahora no hace falta)

# 👇 Crear aplicación con esquema de ciclo de vida
app = FastAPI(lifespan=lifespan)

# 📡 Rutas disponibles
app.include_router(tf_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)