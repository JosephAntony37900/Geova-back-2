# --- main.py ---
from fastapi import FastAPI
from src.routes.sensorTF_routes import router
from src.routes.graph_routes import router as graph_router
from src.controllers.sensorTF_controller import read_and_store
from config import engine
import asyncio
import uvicorn

app = FastAPI()

@app.on_event("startup")
async def startup():
    async def background_task():
        while True:
            await read_and_store(engine)
            await asyncio.sleep(1)  # lectura cada segundo
    asyncio.create_task(background_task())

app.include_router(router)
app.include_router(graph_router)  

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
