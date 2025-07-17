from fastapi import FastAPI
import uvicorn, asyncio

from core.config import get_engine, get_rabbitmq_config

# TF-Luna
from TFLuna.infraestructure.dependencies import init_tf_dependencies
from TFLuna.infraestructure.routes.routes_tf import router as tf_router

# IMX477
from IMX477.infraestructure.dependencies import init_imx_dependencies
from IMX477.infraestructure.routes.routes_imx import router as imx_router

# Graph
from Graph.infraestructure.routes.routes_graph import router as graph_router
from Graph.infraestructure.dependencies import init_graph_dependencies

# MPU6050
from MPU6050.infraestructure.dependencies import init_mpu_dependencies
from MPU6050.infraestructure.routes.routes_mpu import router as mpu_router

app = FastAPI()

engine = get_engine()
rabbitmq_config = get_rabbitmq_config()

init_tf_dependencies(app, engine, rabbitmq_config)
init_imx_dependencies(app, engine, rabbitmq_config)
init_graph_dependencies(app, engine)
init_mpu_dependencies(app, engine, rabbitmq_config)  

@app.on_event("startup")
async def start_tasks():
    async def tf_task():
        while True:
            try:
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=False)
                print("TF-Luna leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                print("❌ Error en TF-Luna:")
                traceback.print_exc()
            await asyncio.sleep(1)

    async def imx_task():
        while True:
            try:
                controller = app.state.imx_controller
                data = await controller.get_imx_data(event=False)
                print("IMX477 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                import traceback
                print("❌ Error en IMX477:")
                traceback.print_exc()
            await asyncio.sleep(3)

    async def mpu_task():
        while True:
            try:
                controller = app.state.mpu_controller
                data = await controller.get_mpu_data(event=False)
                print("MPU6050 leído:", data.dict() if data else "Sin datos")
            except Exception as e:
                print("❌ Error en MPU6050:", e)
            await asyncio.sleep(2)

    asyncio.create_task(tf_task())
    asyncio.create_task(imx_task())
    asyncio.create_task(mpu_task())  

# Rutas
app.include_router(tf_router)
app.include_router(imx_router)
app.include_router(graph_router)
app.include_router(mpu_router)  

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
