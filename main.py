# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn, asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from core.concurrency import connectivity_cache, cleanup as cleanup_concurrency
from core.config import get_local_engine, get_remote_engine, get_rabbitmq_config
from core.cors import setup_cors
from core.connectivity import is_connected  # Nueva versión async con caché
from core.rabbitmq_pool import init_rabbitmq_pool, stop_rabbitmq_pool  # Pool de conexiones
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

async def _check_connectivity() -> bool:
    """Función interna para verificar conectividad via socket (más rápido que HTTP)."""
    import socket
    from concurrent.futures import ThreadPoolExecutor
    
    def check_socket():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("8.8.8.8", 53))  # DNS Google
            sock.close()
            return True
        except Exception:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect(("1.1.1.1", 53))  # Cloudflare backup
                sock.close()
                return True
            except Exception:
                return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, check_socket)

async def is_connected() -> bool:
    """
    Verifica conectividad usando caché para evitar bloqueos.
    El caché tiene TTL de 5 segundos para reducir latencia en peticiones concurrentes.
    """
    return await connectivity_cache.get_or_check(_check_connectivity)
  
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar pool de conexiones RabbitMQ (una sola conexión para todos)
    print("🐰 Inicializando pool de RabbitMQ...")
    init_rabbitmq_pool(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"]  # La config usa "pass" no "password"
    )
    
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

    _cached_internet_status = False
    _last_connectivity_check = 0
    
    # Flag para habilitar/deshabilitar tareas de sensores
    ENABLE_SENSOR_TASKS = True  # Cambiar a False para deshabilitar tareas de background
    SENSOR_TASK_INTERVAL = 5    # Segundos entre lecturas de sensores
    
    async def check_connectivity_periodically():
        """Tarea dedicada para verificar conectividad cada 30 segundos."""
        nonlocal _cached_internet_status, _last_connectivity_check
        import time
        while True:
            try:
                _cached_internet_status = await is_connected()
                _last_connectivity_check = time.time()
                print(f"🌐 Conectividad: {'✅ Online' if _cached_internet_status else '❌ Offline'}")
            except Exception:
                _cached_internet_status = False
            await asyncio.sleep(30)  # Reducido a cada 30 segundos
    
    def get_cached_connectivity():
        """Obtener estado de conectividad sin bloquear."""
        return _cached_internet_status

    async def tf_task():
        """Tarea de lectura TF-Luna con prioridad baja."""
        await asyncio.sleep(2)  # Delay inicial para no saturar al inicio
        while True:
            try:
                # Ceder el event loop ANTES de la operación
                await asyncio.sleep(0)
                
                async with asyncio.timeout(2):
                    controller = app.state.tf_controller
                    data = await controller.get_tf_data(event=False)
                    if data:
                        print("📡 TF-Luna:", data.dict())
                        if not get_cached_connectivity():
                            await ws_manager.send_data(data.dict())
            except asyncio.TimeoutError:
                pass  # Silenciar timeouts
            except Exception:
                pass
            await asyncio.sleep(SENSOR_TASK_INTERVAL)

    async def imx_task():
        """Tarea de lectura IMX477 con prioridad baja."""
        from IMX477.infraestructure.streaming.streamer import get_streamer
        streamer = get_streamer()
        await asyncio.sleep(3)  # Delay inicial
        
        while True:
            try:
                await asyncio.sleep(0)  # Ceder event loop
                
                async with asyncio.timeout(3):
                    if streamer.is_streaming:
                        frame = streamer.get_current_frame()
                        if frame is not None:
                            controller = app.state.imx_controller
                            data = await controller.get_imx_data(event=False)
                            if data and not get_cached_connectivity():
                                await ws_manager_imx.send_data(data.dict())
                    else:
                        controller = app.state.imx_controller
                        data = await controller.get_imx_data(event=False)
                        if data and not get_cached_connectivity():
                            await ws_manager_imx.send_data(data.dict())
            except (asyncio.TimeoutError, Exception):
                pass
            await asyncio.sleep(SENSOR_TASK_INTERVAL + 2)  # Más lento que otros

    async def mpu_task():
        """Tarea de lectura MPU6050 con prioridad baja."""
        await asyncio.sleep(4)  # Delay inicial
        while True:
            try:
                await asyncio.sleep(0)  # Ceder event loop
                
                async with asyncio.timeout(2):
                    controller = app.state.mpu_controller
                    data = await controller.get_mpu_data(event=False)
                    if data and not get_cached_connectivity():
                        await ws_manager_mpu.send_data(data.dict())
            except (asyncio.TimeoutError, Exception):
                pass
            await asyncio.sleep(SENSOR_TASK_INTERVAL)

    async def hc_task():
        """Tarea de lectura HC-SR04 BLE con prioridad baja."""
        await asyncio.sleep(5)  # Delay inicial más largo para BLE
        
        controller = app.state.hc_controller
        reader = controller.usecase.reader
        connection_attempts = 0
        max_connection_attempts = 3
        
        print("🔵 HC-SR04: Iniciando tarea de lectura BLE...")
        
        # Intentar conexión inicial
        while connection_attempts < max_connection_attempts:
            await asyncio.sleep(0)  # Ceder event loop
            print(f"🔵 HC-SR04: Intento de conexión {connection_attempts + 1}/{max_connection_attempts}")
            try:
                async with asyncio.timeout(5):
                    if await reader.connect():
                        print("HC-SR04: Conexión inicial establecida")
                        break
            except asyncio.TimeoutError:
                print("HC-SR04: Timeout en conexión")
            connection_attempts += 1
            if connection_attempts < max_connection_attempts:
                await asyncio.sleep(10)
        
        if connection_attempts >= max_connection_attempts:
            print("HC-SR04: No se pudo establecer conexión inicial")
        
        # Loop principal con prioridad baja
        while True:
            try:
                await asyncio.sleep(0)  # Ceder event loop PRIMERO
                
                if not reader.is_connected:
                    await asyncio.sleep(15)  # Esperar más si no hay conexión
                    try:
                        async with asyncio.timeout(5):
                            await reader.connect()
                    except asyncio.TimeoutError:
                        pass
                    continue
                
                async with asyncio.timeout(2):
                    data = await controller.get_hc_data(project_id=1, event=False)
                    if data and not get_cached_connectivity():
                        await ws_manager_hc.send_data(data.dict())
                                                                                
            except asyncio.CancelledError:
                break
            except (asyncio.TimeoutError, Exception):
                pass
                                                
            await asyncio.sleep(SENSOR_TASK_INTERVAL + 1)
        
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
                if get_cached_connectivity():
                    await sync_tf_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync TF-Luna: {e}")
                await asyncio.sleep(30)

    async def sync_imx():
        print("Iniciando sincronización IMX477...")
        while True:
            try:
                if get_cached_connectivity():
                    await sync_imx_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync IMX477: {e}")
                await asyncio.sleep(30)

    async def sync_mpu():
        print("Iniciando sincronización MPU6050...")
        while True:
            try:
                if get_cached_connectivity():
                    await sync_mpu_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync MPU6050: {e}")
                await asyncio.sleep(30)

    async def sync_hc():
        print("Iniciando sincronización HC-SR04...")
        while True:
            try:
                if get_cached_connectivity():
                    await sync_hc_pending_data(local_session, remote_session, is_connected)
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error en sync HC-SR04: {e}")
                await asyncio.sleep(30)

    print("Creando tarea de verificación de conectividad...")
    asyncio.create_task(check_connectivity_periodically())
    
    if ENABLE_SENSOR_TASKS:
        print("Creando tareas de sensores (HABILITADAS)...")
        asyncio.create_task(tf_task())
        asyncio.create_task(imx_task())
        asyncio.create_task(mpu_task())
        asyncio.create_task(hc_task())
        
        print("Creando tareas de sincronización...")
        asyncio.create_task(sync_tf())
        asyncio.create_task(sync_imx())
        asyncio.create_task(sync_mpu())
        asyncio.create_task(sync_hc())
    else:
        print("⚠️ Tareas de sensores DESHABILITADAS (ENABLE_SENSOR_TASKS=False)")
    
    print("📷 Streaming de IMX477 listo para usar")
    yield
    print("Cerrando aplicación...")
    cleanup_concurrency()
    print("🐰 Cerrando pool de RabbitMQ...")
    stop_rabbitmq_pool()

app = FastAPI(
    title="Raspberry Pi Sensor API",
    description="API para sensores IMX477, TF-Luna, MPU6050 con streaming de video en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================
# MANEJADORES DE ERRORES GLOBALES
# ============================================
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Manejador para errores de validación de Pydantic.
    Devuelve mensajes de error claros y específicos.
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append({
            "campo": field,
            "mensaje": message,
            "tipo_error": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Error de validación en los datos enviados",
            "detalles": errors,
            "codigo": 422
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """
    Manejador para excepciones HTTP (404, 500, etc.).
    Devuelve mensajes descriptivos.
    """
    mensajes = {
        400: "Solicitud incorrecta",
        401: "No autorizado",
        403: "Acceso prohibido",
        404: "Recurso no encontrado",
        405: "Método no permitido",
        408: "Tiempo de espera agotado",
        429: "Demasiadas solicitudes",
        500: "Error interno del servidor",
        502: "Error de puerta de enlace",
        503: "Servicio no disponible",
        504: "Tiempo de espera de la puerta de enlace agotado"
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail if exc.detail else mensajes.get(exc.status_code, "Error desconocido"),
            "codigo": exc.status_code,
            "mensaje_general": mensajes.get(exc.status_code, "Error desconocido")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """
    Manejador para cualquier excepción no capturada.
    """
    import traceback
    print(f"Error no manejado: {exc}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "codigo": 500,
            "mensaje_general": "Error interno del servidor. Contacte al administrador si el problema persiste."
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://raspberrypi.local:3000",
        "http://raspberrypi.local:5173",
        "http://raspberrypi.local",
        "http://192.168.*",
        "http://10.*",
        "http://172.16.*",
        "https://www.geova.pro",
        "https://geova.pro",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
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
def root():
    """Endpoint raíz SÍNCRONO."""
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
            "health": "/health",
            "ping": "/ping"
        }
    }


@app.get("/ping")
@app.head("/ping")
def ping():
    """
    Endpoint SÍNCRONO ultra-ligero para verificar que la API está viva.
    No usa async para evitar cualquier bloqueo del event loop.
    """
    return {"pong": True}


@app.get("/health")
@app.head("/health")
def health_check():
    """
    Health check SÍNCRONO - responde inmediatamente sin tocar el event loop.
    Útil para que el frontend verifique si la API está disponible.
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }


@app.get("/health/detailed")
async def health_check_detailed():
    """
    Health check detallado con información de todos los servicios.
    Puede tardar más porque verifica conectividad real.
    """
    from IMX477.infraestructure.streaming.streamer import get_streamer
    from core.concurrency import (
        DB_SEMAPHORE_LOCAL, DB_SEMAPHORE_REMOTE, 
        RATE_LIMITERS, connectivity_cache
    )
    
    streamer = get_streamer()
    streaming_status = streamer.get_status()
    
    connection_status = await is_connected()
    
    # Información de concurrencia
    concurrency_info = {
        "db_local_available": DB_SEMAPHORE_LOCAL._value,
        "db_local_max": 10,
        "db_remote_available": DB_SEMAPHORE_REMOTE._value,
        "db_remote_max": 5,
        "connectivity_cached": connectivity_cache.get() is not None,
        "connectivity_cache_ttl": 5.0
    }
    
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
        },
        "concurrency": concurrency_info
    }


@app.get("/metrics")
async def get_metrics():
    """Endpoint para monitorear métricas de concurrencia y rendimiento."""
    from core.concurrency import (
        DB_SEMAPHORE_LOCAL, DB_SEMAPHORE_REMOTE,
        RATE_LIMITERS, connectivity_cache
    )
    
    return {
        "semaphores": {
            "db_local": {
                "available": DB_SEMAPHORE_LOCAL._value,
                "max": 10,
                "usage_percent": round((10 - DB_SEMAPHORE_LOCAL._value) / 10 * 100, 1)
            },
            "db_remote": {
                "available": DB_SEMAPHORE_REMOTE._value,
                "max": 5,
                "usage_percent": round((5 - DB_SEMAPHORE_REMOTE._value) / 5 * 100, 1)
            }
        },
        "rate_limiters": {
            sensor: {
                "tokens_available": round(limiter._tokens, 2),
                "capacity": limiter.capacity,
                "rate_per_second": limiter.rate
            }
            for sensor, limiter in RATE_LIMITERS.items()
        },
        "connectivity_cache": {
            "is_cached": connectivity_cache.get() is not None,
            "cached_value": connectivity_cache.get(),
            "ttl_seconds": connectivity_cache._ttl
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
        access_log=True,
        limit_concurrency=100,
        limit_max_requests=None,
        timeout_keep_alive=5,
    )