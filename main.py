# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
import aiohttp

from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from core.cors import setup_cors
from TFLuna.infraestructure.sync.sync_service import sync_tf_pending_data
from IMX477.infraestructure.sync.sync_service import sync_imx_pending_data
from MPU6050.infraestructure.sync.sync_service import sync_mpu_pending_data
from HCSR04.infraestructure.sync.sync_service import sync_hc_pending_data

from TFLuna.infraestructure.dependencies import init_tf_dependencies
from IMX477.infraestructure.dependencies import init_imx_dependencies
from MPU6050.infraestructure.dependencies import init_mpu_dependencies
from HCSR04.infraestructure.dependencies import init_hc_dependencies

from TFLuna.infraestructure.routes.routes_tf import router as tf_router
from IMX477.infraestructure.routes.routes_imx import router as imx_router
from IMX477.infraestructure.routes.streaming_routes import router as streaming_router
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

async def is_connected() -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://example.com", timeout=3) as response:
                return response.status == 200
    except Exception as e:
        print(f"Error verificando conexión: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tf_dependencies(app, local_session, remote_session, rabbitmq_config)
    init_imx_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected)
    init_mpu_dependencies(app, local_session, remote_session, rabbitmq_config, is_connected)
    init_hc_dependencies(
        app, 
        local_session, 
        remote_session, 
        rabbitmq_config, 
        is_connected, 
        device_name="ESP32_SensorBLE",
        char_uuid="beb5483e-36e1-4688-b7f5-ea07361b26a8"
    )

    async def create_tables(engine: AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(TFBase.metadata.create_all)
            await conn.run_sync(IMXBase.metadata.create_all)
            await conn.run_sync(MPUBase.metadata.create_all)
            await conn.run_sync(HCBase.metadata.create_all)

    await create_tables(local_session.kw["bind"])

    connection_status = await is_connected()
    
    if connection_status:
        try:
            await create_tables(remote_session.kw["bind"])
            print("Tablas remotas creadas/verificadas :)")
        except Exception as e:
            print(f"Error creando tablas remotas: {e}")
    else:
        print("🔌 Sin conexión: se omitió la creación de tablas remotas :(")

    async def tf_task():
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.tf_controller
                data = await controller.get_tf_data(event=False)
                print("📡 TF-Luna:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager.send_data(data.dict())
            except Exception:
                import traceback
                print("Error en TF-Luna:")
                traceback.print_exc()
            await asyncio.sleep(1)

    async def imx_task():
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.imx_controller
                data = await controller.get_imx_data(event=False)
                print("📷 IMX477:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager_imx.send_data(data.dict())
            except Exception:
                import traceback
                print("Error en IMX477:")
                traceback.print_exc()
            await asyncio.sleep(2)

    async def mpu_task():
        while True:
            try:
                internet_available = await is_connected()
                controller = app.state.mpu_controller
                data = await controller.get_mpu_data(event=False)
                print("🌀 MPU6050:", data.dict() if data else "Sin datos")
                if not internet_available and data:
                    await ws_manager_mpu.send_data(data.dict())
            except Exception:
                import traceback
                print("Error en MPU6050:")
                traceback.print_exc()
            await asyncio.sleep(1)

    async def hc_task():
        controller = app.state.hc_controller
        reader = controller.usecase.reader
        connection_attempts = 0
        max_connection_attempts = 5
        
        print("🔵 HC-SR04: Iniciando tarea de lectura BLE...")
        
        while connection_attempts < max_connection_attempts:
                print(f"🔵 HC-SR04: Intento de conexión {connection_attempts + 1}/{max_connection_attempts}")
                if await reader.connect():
                        print("HC-SR04: Conexión inicial establecida")
                        break
                else:
                        connection_attempts += 1
                        if connection_attempts < max_connection_attempts:
                                print(f"HC-SR04: Fallo de conexión, esperando 5s...")
                                await asyncio.sleep(5)
        
        if connection_attempts >= max_connection_attempts:
                print("HC-SR04: No se pudo establecer conexión inicial, reintentando cada 30s...")
        
        while True:
                try:
                        internet_available = await is_connected()
                        
                        if not reader.is_connected:
                                print("🔵 HC-SR04: Sin conexión, intentando reconectar...")
                                if await reader.connect():
                                        print("✅ HC-SR04: Reconectado exitosamente")
                                else:
                                        print("HC-SR04: Fallo de reconexión, esperando 10s...")
                                        await asyncio.sleep(10)
                                        continue
                        
                        if reader.client and not reader.client.is_connected:
                                print("🔵 HC-SR04: Cliente desconectado, limpiando estado...")
                                reader.is_connected = False
                                await reader.disconnect()
                                continue
                        
                        if reader.is_connected:
                                data = await controller.get_hc_data(project_id=1, event=False)

                                if data:
                                        print(f"🔵 HC-SR04 BLE: {data.distancia_cm} cm")
                                        
                                        if not internet_available:
                                                await ws_manager_hc.send_data(data.dict())
                                else:
                                        print("🔵 HC-SR04: Sin datos del ESP32 (posiblemente apagado)")
                                        
                                        if reader.client and not reader.client.is_connected:
                                                print("🔵 HC-SR04: Conexión BLE perdida, desconectando...")
                                                reader.is_connected = False
                                                await reader.disconnect()
                                                                                
                except asyncio.CancelledError:
                        print("HC-SR04: Tarea cancelada")
                        break
                except KeyboardInterrupt:
                        print("HC-SR04: Interrupción por teclado")
                        break
                except Exception as e:
                        import traceback
                        print("Error en HC-SR04:")
                        print(f"Error: {e}")
                        traceback.print_exc()
                        
                        try:
                                if reader.is_connected:
                                        await reader.disconnect()
                        except:
                                pass
                                                
                await asyncio.sleep(2)
        
        try:
                if reader.is_connected:
                        await reader.disconnect()
                        print("🔵 HC-SR04: Desconectado al finalizar tarea")
        except:
                pass

    async def sync_tf():
        print("Iniciando sincronización TF-Luna...")
        while True:
            try:
                if await is_connected():
                    await sync_tf_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync TF-Luna: {e}")
                await asyncio.sleep(30)

    async def sync_imx():
        print("Iniciando sincronización IMX477...")
        while True:
            try:
                if await is_connected():
                    await sync_imx_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync IMX477: {e}")
                await asyncio.sleep(30)

    async def sync_mpu():
        print("Iniciando sincronización MPU6050...")
        while True:
            try:
                if await is_connected():
                    await sync_mpu_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync MPU6050: {e}")
                await asyncio.sleep(30)

    async def sync_hc():
        print("Iniciando sincronización HC-SR04...")
        while True:
            try:
                if await is_connected():
                    await sync_hc_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync HC-SR04: {e}")
                await asyncio.sleep(30)

    print("Creando tareas de sensores...")
    asyncio.create_task(tf_task())
    asyncio.create_task(imx_task())
    asyncio.create_task(mpu_task())
    asyncio.create_task(hc_task())

    print("Creando tareas de sincronización...")
    asyncio.create_task(sync_tf())
    asyncio.create_task(sync_imx())
    asyncio.create_task(sync_mpu())
    asyncio.create_task(sync_hc())
    print("📷 Streaming de IMX477 listo para usar")
    yield
    print("Cerrando aplicación...")

app = FastAPI(
    title="Raspberry Pi Sensor API",
    description="API para sensores IMX477, TF-Luna, MPU6050 con streaming de video en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

setup_cors(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://raspberrypi.local:3000",
        "http://raspberrypi.local:5173",
        "http://raspberrypi.local",
        "http://192.168.*",
        "http://10.*",
        "http://172.16.*",
        "https://www.geova.pro",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(router_ws_tf)
app.include_router(router_ws_mpu)
app.include_router(router_ws_imx)
app.include_router(router_ws_hc)

app.include_router(tf_router, tags=["TF-Luna"])
app.include_router(imx_router, tags=["IMX477"])
app.include_router(streaming_router, tags=["Streaming"])
app.include_router(mpu_router, tags=["MPU6050"])
app.include_router(hc_router, tags=["HC-SR04"])

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
    from IMX477.infraestructure.streaming.streamer import Streamer
    
    temp_streamer = Streamer()
    streaming_status = temp_streamer.get_status()
    
    connection_status = await is_connected()
    
    return {
        "status": "healthy",
        "timestamp": "2025-01-15T12:00:00Z",
        "services": {
            "database": "connected" if connection_status else "local_only",
            "sensors": "active",
            "streaming": {
                "available": True,
                "active": streaming_status["active"],
                "fps": streaming_status["fps"]
            },
            "internet": "connected" if connection_status else "disconnected"
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