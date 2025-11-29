# core/concurrency.py
"""
Módulo de utilidades de concurrencia para evitar saturación de la API.
Implementa:
- Semáforos para limitar consultas concurrentes a BD
- Caché de conectividad con TTL
- Timeouts configurables
- ThreadPoolExecutor compartido
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN GLOBAL DE CONCURRENCIA
# ============================================================================

# Semáforos para limitar acceso concurrente a recursos
DB_SEMAPHORE_LOCAL = asyncio.Semaphore(10)    # Max 10 consultas locales simultáneas
DB_SEMAPHORE_REMOTE = asyncio.Semaphore(5)    # Max 5 consultas remotas simultáneas
CONNECTIVITY_SEMAPHORE = asyncio.Semaphore(1) # Solo 1 check de conectividad a la vez

# ThreadPoolExecutor compartido para operaciones bloqueantes
SHARED_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="Geova")

# Timeouts (segundos)
DB_QUERY_TIMEOUT = 5.0  # Reducido de 10s a 5s para evitar bloqueos largos
CONNECTIVITY_TIMEOUT = 2.0  # Reducido de 3s a 2s

# ============================================================================
# CACHÉ DE CONECTIVIDAD
# ============================================================================

class ConnectivityCache:
    """Caché con TTL para estado de conectividad."""
    
    def __init__(self, ttl_seconds: float = 5.0):
        self._is_connected: Optional[bool] = None
        self._last_check: float = 0.0
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    def is_expired(self) -> bool:
        return time.time() - self._last_check > self._ttl
    
    def get(self) -> Optional[bool]:
        if self.is_expired():
            return None
        return self._is_connected
    
    def set(self, value: bool):
        self._is_connected = value
        self._last_check = time.time()
    
    async def get_or_check(self, check_func: Callable) -> bool:
        """Obtiene del caché o ejecuta el check si está expirado."""
        cached = self.get()
        if cached is not None:
            return cached
        
        async with self._lock:
            # Double-check después de adquirir el lock
            cached = self.get()
            if cached is not None:
                return cached
            
            try:
                async with asyncio.timeout(CONNECTIVITY_TIMEOUT):
                    result = await check_func()
                    self.set(result)
                    return result
            except asyncio.TimeoutError:
                logger.warning("Timeout verificando conectividad, asumiendo offline")
                self.set(False)
                return False
            except Exception as e:
                logger.warning(f"Error verificando conectividad: {e}")
                self.set(False)
                return False

# Instancia global del caché de conectividad
connectivity_cache = ConnectivityCache(ttl_seconds=5.0)

# ============================================================================
# DECORADORES PARA CONCURRENCIA
# ============================================================================

def with_db_semaphore(is_remote: bool = False):
    """
    Decorador que limita las consultas concurrentes a la BD.
    
    Args:
        is_remote: Si True, usa el semáforo de BD remota (más restrictivo)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            semaphore = DB_SEMAPHORE_REMOTE if is_remote else DB_SEMAPHORE_LOCAL
            
            try:
                # Intentar adquirir con timeout
                async with asyncio.timeout(DB_QUERY_TIMEOUT):
                    async with semaphore:
                        return await func(*args, **kwargs)
            except asyncio.TimeoutError:
                logger.error(f"Timeout en {func.__name__}: demasiadas consultas concurrentes")
                raise TimeoutError(f"La base de datos está saturada, intente más tarde")
        
        return wrapper
    return decorator


def with_timeout(seconds: float):
    """Decorador para agregar timeout a funciones async."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async with asyncio.timeout(seconds):
                    return await func(*args, **kwargs)
            except asyncio.TimeoutError:
                logger.error(f"Timeout en {func.__name__} después de {seconds}s")
                raise
        return wrapper
    return decorator


def run_in_executor(func: Callable) -> Callable:
    """Ejecuta una función síncrona en el ThreadPoolExecutor compartido."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            SHARED_EXECUTOR,
            lambda: func(*args, **kwargs)
        )
    return wrapper

# ============================================================================
# FUNCIONES HELPER
# ============================================================================

async def gather_with_concurrency(limit: int, *tasks):
    """
    Ejecuta múltiples tareas con un límite de concurrencia.
    Útil para batch de consultas a BD.
    
    Args:
        limit: Número máximo de tareas ejecutándose simultáneamente
        *tasks: Coroutines a ejecutar
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def sem_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def first_completed(*coros, timeout: float = None):
    """
    Retorna el resultado de la primera coroutine que complete.
    Útil para fallback local/remoto.
    """
    tasks = [asyncio.create_task(coro) for coro in coros]
    
    try:
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancelar las tareas pendientes
        for task in pending:
            task.cancel()
        
        if done:
            return done.pop().result()
        return None
        
    except Exception as e:
        for task in tasks:
            task.cancel()
        raise e


class RateLimiter:
    """
    Rate limiter simple para endpoints críticos.
    Usa el algoritmo de token bucket.
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens por segundo
            capacity: Capacidad máxima del bucket
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Intenta adquirir un token. Retorna False si no hay disponibles."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_update = now
            
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False
    
    async def wait_for_token(self, timeout: float = None) -> bool:
        """Espera hasta obtener un token o timeout."""
        start = time.time()
        while True:
            if await self.acquire():
                return True
            
            if timeout and (time.time() - start) >= timeout:
                return False
            
            await asyncio.sleep(0.1)


# Rate limiters por sensor (20 requests/segundo con burst de 30)
RATE_LIMITERS = {
    "imx477": RateLimiter(rate=20, capacity=30),
    "tfluna": RateLimiter(rate=20, capacity=30),
    "mpu6050": RateLimiter(rate=20, capacity=30),
    "hcsr04": RateLimiter(rate=20, capacity=30),
}


def cleanup():
    """Limpia recursos al cerrar la aplicación."""
    SHARED_EXECUTOR.shutdown(wait=False)
