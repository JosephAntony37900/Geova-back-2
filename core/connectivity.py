# core/connectivity.py
"""
Módulo de conectividad con caché para evitar múltiples verificaciones.
Patrón: Singleton con caché temporal + async
"""
import asyncio
import socket
import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

class ConnectivityManager:
    """
    Gestiona el estado de conectividad con caché para evitar
    múltiples verificaciones simultáneas.
    """
    _instance: Optional['ConnectivityManager'] = None
    _executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="connectivity")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._is_connected: bool = False
        self._last_check: float = 0
        self._cache_duration: float = 15.0  # Cachear resultado por 15 segundos
        self._lock = asyncio.Lock()
        self._checking = False
    
    def _check_sync(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 3) -> bool:
        """Verificación sincrónica de conectividad."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            return True
        except Exception:
            # Intentar con servidor alternativo si falla
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                sock.connect(("1.1.1.1", 53))  # Cloudflare DNS como backup
                sock.close()
                return True
            except Exception:
                return False
    
    async def is_connected(self) -> bool:
        """
        Verifica conectividad con caché.
        Evita múltiples verificaciones simultáneas.
        """
        current_time = time.time()
        
        # Si el caché es válido, retornar valor cacheado
        if current_time - self._last_check < self._cache_duration:
            return self._is_connected
        
        # Evitar verificaciones simultáneas
        if self._checking:
            return self._is_connected
        
        async with self._lock:
            # Doble verificación después de obtener el lock
            current_time = time.time()
            if current_time - self._last_check < self._cache_duration:
                return self._is_connected
            
            self._checking = True
            try:
                loop = asyncio.get_event_loop()
                self._is_connected = await loop.run_in_executor(
                    self._executor, self._check_sync
                )
            except Exception:
                self._is_connected = False
            finally:
                self._last_check = time.time()
                self._checking = False
        
        return self._is_connected
    
    def get_cached_status(self) -> bool:
        """Obtiene el estado cacheado sin verificar (no bloqueante)."""
        return self._is_connected
    
    async def force_check(self) -> bool:
        """Fuerza una verificación ignorando el caché."""
        self._last_check = 0
        return await self.is_connected()


# Singleton global
_connectivity_manager: Optional[ConnectivityManager] = None

def get_connectivity_manager() -> ConnectivityManager:
    """Obtiene la instancia global del gestor de conectividad."""
    global _connectivity_manager
    if _connectivity_manager is None:
        _connectivity_manager = ConnectivityManager()
    return _connectivity_manager

async def is_connected() -> bool:
    """Función helper async para verificar conectividad (usa caché)."""
    return await get_connectivity_manager().is_connected()

# Mantener compatibilidad con código síncrono existente
def is_connected_sync(host: str = "8.8.8.8", port: int = 53, timeout: float = 3) -> bool:
    """Versión síncrona (legacy) - usar is_connected() cuando sea posible."""
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.close()
        return True
    except Exception:
        return False