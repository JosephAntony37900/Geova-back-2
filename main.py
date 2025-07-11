# main.py
from fastapi import FastAPI
import uvicorn, asyncio

from core.config import get_engine, get_rabbitmq_config
from TFLuna.infraestructure.dependencies import init_tf_dependencies
from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from IMX477.infraestructure.dependencies import init_imx_dependencies
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from Graph.infraestructure.routes.routes_graph import router as graph_router
from Graph.infraestructure.dependencies import init_graph_dependencies

app = FastAPI()

# Obtener configuración
engine = get_engine()
rabbitmq_config = get_rabbitmq_config()

# Inyectar dependencias
init_tf_dependencies(app, engine, rabbitmq_config)
init_imx_dependencies(app, engine, rabbitmq_config)
init_graph_dependencies(app, engine)

@app.on_event("startup")
async def start_tasks():
    async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=False)
                print("TF-Luna leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                print("❌ Error en TF-Luna:", e)
            await asyncio.sleep(1)

    async def imx_task():
        while True:
            try:
                controller = app.state.imx_controller
                data = await controller.get_imx_data(event=False)
                print("IMX477 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                print("❌ Error en IMX477:", e)
            await asyncio.sleep(3)

    asyncio.create_task(tf_task())
    asyncio.create_task(imx_task())

# Rutas
app.include_router(tf_router)
app.include_router(imx_router)
app.include_router(graph_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
