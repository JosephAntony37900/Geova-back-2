# --- main.py ---
from fastapi import FastAPI
from config import engine
import asyncio
import uvicorn

from src.routes.sensorTF_routes import router as tf_router
from src.routes.sensorIMX477_routes import router as imx477_router
from src.routes.graph_routes import router as graph_router
from src.routes.ws_routes import router as ws_router

from src.controllers.sensorTF_controller import read_and_store
from src.controllers.sensorIMX477_controller import analizar_frame
from src.websocket.ws_manager import manager as ws_manager  # 🚨 Nuevo import

app = FastAPI()

@app.on_event("startup")
async def tf_task():
    while True:
        try:
            data = await read_and_store(engine)
            if data:
                await ws_manager.broadcast({"sensor": "TF-Luna", "data": data.dict()})
        except Exception as e:
            print("Error en TF-Luna:", e)
        await asyncio.sleep(1)


    async def imx_task():
        while True:
            try:
                data = await analizar_frame(engine)
                if data:
                    await ws_manager.broadcast({"sensor": "IMX477", "data": data.dict()})
            except Exception as e:
                print("Error en IMX477:", e)
            await asyncio.sleep(3)

    asyncio.create_task(tf_task())
    asyncio.create_task(imx_task())

# Registrar rutas HTTP y WebSocket
app.include_router(tf_router)
app.include_router(imx477_router)
app.include_router(graph_router)
app.include_router(ws_router)  # 🔌 WebSocket

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
