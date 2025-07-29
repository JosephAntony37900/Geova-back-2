# TFLuna/infraestructure/ws/ws_manager.py - VERSIÓN CORREGIDA
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
from core.connectivity import is_connected
import asyncio
import json
import logging
from datetime import datetime
import threading

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_check_task: Optional[asyncio.Task] = None
        self._check_interval = 5
        self._message_count = 0
        self._lock = asyncio.Lock()  # Para evitar race conditions
        self._last_connection_check = None
        self._force_offline_mode = False  # Para debugging

    async def connect(self, websocket: WebSocket):
        async with self._lock:  # Usar lock para operaciones críticas
            try:
                await websocket.accept()
                logger.info("🔌 WebSocket connection attempt started")
                
                # Verificar internet con timeout más corto para debugging
                internet_available = await self._check_internet_with_timeout()
                logger.info(f"🌐 Internet status check result: {'Available' if internet_available else 'Offline'}")
                
                # Modo debug: forzar offline
                if self._force_offline_mode:
                    internet_available = False
                    logger.info("🚫 MODO DEBUG: Forzando modo offline")
                
                if internet_available and not self._force_offline_mode:
                    await self._send_rejection_message(
                        websocket,
                        "El WebSocket solo está disponible cuando no hay conexión a internet"
                    )
                    return False
                
                # Agregar conexión ANTES de enviar mensajes
                self.active_connections.append(websocket)
                logger.info(f"✅ Cliente WebSocket AGREGADO - Total conexiones: {len(self.active_connections)}")
                
                # Enviar mensaje de bienvenida
                welcome_message = {
                    "type": "connection_status",
                    "status": "connected",
                    "message": "Conexión WebSocket establecida correctamente",
                    "timestamp": datetime.utcnow().isoformat(),
                    "sensor_type": "TF-Luna",
                    "debug": True,
                    "connection_id": len(self.active_connections)
                }
                
                await websocket.send_json(welcome_message)
                logger.info(f"📤 Mensaje de bienvenida enviado - Conexiones activas: {len(self.active_connections)}")
                
                # Iniciar monitoreo si es la primera conexión
                if len(self.active_connections) == 1:
                    self._start_connection_monitoring()
                
                # Enviar mensaje de test inmediato
                test_message = {
                    "type": "immediate_test",
                    "message": "Conexión establecida - Test inmediato",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connections_count": len(self.active_connections)
                }
                await websocket.send_json(test_message)
                logger.info("🧪 Mensaje de test inmediato enviado")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Error durante la conexión WebSocket: {str(e)}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
                try:
                    await websocket.close(code=1011, reason="Internal server error")
                except:
                    pass
                return False

    async def _check_internet_with_timeout(self, timeout=3):
        """Verificar internet con timeout personalizado"""
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(is_connected), 
                timeout=timeout
            )
            self._last_connection_check = {
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            return result
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout verificando internet ({timeout}s) - Asumiendo offline")
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando internet: {e}")
            return False

    def disconnect(self, websocket: WebSocket):
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"🔌 Cliente WebSocket REMOVIDO - Restantes: {len(self.active_connections)}")
                
                # Cancelar monitoreo si no hay conexiones
                if not self.active_connections and self._connection_check_task:
                    self._connection_check_task.cancel()
                    self._connection_check_task = None
                    logger.info("🛑 Monitoreo de conexiones cancelado")
        except Exception as e:
            logger.error(f"❌ Error en disconnect: {e}")

    async def send_data(self, data: dict):
        """Método principal para enviar datos - CON DEBUGGING DETALLADO"""
        async with self._lock:
            # Log detallado del estado actual
            logger.info(f"📊 SEND_DATA INICIADO:")
            logger.info(f"   - Conexiones activas: {len(self.active_connections)}")
            logger.info(f"   - Datos a enviar: {data}")
            logger.info(f"   - Mensaje count: {self._message_count}")
            
            if not self.active_connections:
                logger.warning("⚠️ SEND_DATA: No hay conexiones WebSocket activas - SALIENDO")
                return

            # Verificar internet SOLO si no estamos en modo debug
            if not self._force_offline_mode:
                internet_available = await self._check_internet_with_timeout(timeout=2)
                logger.info(f"🌐 SEND_DATA: Internet check = {internet_available}")
                
                if internet_available:
                    logger.info("🌐 SEND_DATA: Internet detectado - Cerrando conexiones WebSocket")
                    await self._close_all_connections(
                        reason="Conexión a internet restablecida",
                        code=1000
                    )
                    return
            else:
                logger.info("🚫 SEND_DATA: Modo debug - Saltando verificación de internet")

            # Preparar mensaje con metadata
            enhanced_data = {
                **data,
                "message_id": self._message_count,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "sensor_data",
                "sensor_type": "TF-Luna",
                "total_connections": len(self.active_connections)
            }
            
            self._message_count += 1
            logger.info(f"📤 SEND_DATA: Enviando mensaje #{self._message_count} a {len(self.active_connections)} conexiones")

            # Enviar a todas las conexiones
            disconnected = []
            successful_sends = 0
            
            for i, conn in enumerate(self.active_connections):
                try:
                    logger.info(f"📤 Enviando a conexión #{i}...")
                    await conn.send_json(enhanced_data)
                    successful_sends += 1
                    logger.info(f"✅ Enviado exitosamente a conexión #{i}")
                    
                except (WebSocketDisconnect, RuntimeError) as e:
                    logger.warning(f"⚠️ WebSocket error en conexión #{i}: {str(e)}")
                    disconnected.append(conn)
                except Exception as e:
                    logger.error(f"❌ Error inesperado en conexión #{i}: {str(e)}")
                    disconnected.append(conn)

            # Limpiar conexiones muertas
            for conn in disconnected:
                self.disconnect(conn)
                
            logger.info(f"📊 SEND_DATA COMPLETADO:")
            logger.info(f"   - Envíos exitosos: {successful_sends}")
            logger.info(f"   - Conexiones desconectadas: {len(disconnected)}")
            logger.info(f"   - Conexiones restantes: {len(self.active_connections)}")

    def enable_debug_mode(self):
        """Habilitar modo debug (forzar offline)"""
        self._force_offline_mode = True
        logger.info("🚫 MODO DEBUG HABILITADO - WebSocket funcionará aunque haya internet")

    def disable_debug_mode(self):
        """Deshabilitar modo debug"""
        self._force_offline_mode = False
        logger.info("✅ MODO DEBUG DESHABILITADO - WebSocket funcionará solo offline")

    async def send_heartbeat(self):
        """Enviar heartbeat a todas las conexiones"""
        if self.active_connections:
            heartbeat_data = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "connections_count": len(self.active_connections),
                "message_count": self._message_count
            }
            logger.info(f"💓 Enviando heartbeat a {len(self.active_connections)} conexiones")
            await self.send_data(heartbeat_data)

    def _start_connection_monitoring(self):
        if not self._connection_check_task or self._connection_check_task.done():
            self._connection_check_task = asyncio.create_task(self._monitor_connections())
            logger.info("🔍 Monitoreo de conexiones INICIADO")

    async def _monitor_connections(self):
        """Monitor mejorado con heartbeat"""
        heartbeat_counter = 0
        
        while self.active_connections:
            try:
                # Enviar heartbeat cada 10 ciclos (50 segundos)
                if heartbeat_counter % 10 == 0:
                    await self.send_heartbeat()
                
                heartbeat_counter += 1
                
                # Verificar internet solo si no estamos en modo debug
                if not self._force_offline_mode:
                    if await self._check_internet_with_timeout(timeout=2):
                        logger.info("🌐 Monitor: Internet detectado - Cerrando conexiones")
                        await self._close_all_connections(
                            reason="Conexión a internet detectada",
                            code=1000
                        )
                        break
                
                await asyncio.sleep(self._check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error en monitoreo de conexión: {str(e)}")
                break

    async def _close_all_connections(self, reason: str, code: int = 1000):
        if not self.active_connections:
            return

        logger.info(f"🛑 Cerrando {len(self.active_connections)} conexiones: {reason}")
        
        close_message = {
            "type": "connection_status",
            "status": "closing",
            "message": reason,
            "code": code,
            "timestamp": datetime.utcnow().isoformat()
        }

        for i, conn in enumerate(self.active_connections[:]):
            try:
                await conn.send_json(close_message)
                await conn.close(code=code, reason=reason)
                logger.info(f"✅ Conexión #{i} cerrada correctamente")
            except Exception as e:
                logger.warning(f"⚠️ Error al cerrar conexión #{i}: {str(e)}")
            finally:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

    async def _send_rejection_message(self, websocket: WebSocket, message: str):
        try:
            rejection_message = {
                "type": "connection_status",
                "status": "rejected",
                "message": message,
                "action": "reconnect_when_offline",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(rejection_message)
            logger.info(f"❌ Mensaje de rechazo enviado: {message}")
            await websocket.close(code=1000, reason=message)
        except Exception as e:
            logger.error(f"❌ Error al enviar mensaje de rechazo: {str(e)}")
            try:
                await websocket.close(code=1011, reason="Internal error sending rejection")
            except:
                pass

    def get_stats(self):
        """Obtener estadísticas detalladas"""
        return {
            "active_connections": len(self.active_connections),
            "messages_sent": self._message_count,
            "monitoring_active": self._connection_check_task is not None and not self._connection_check_task.done(),
            "debug_mode": self._force_offline_mode,
            "last_connection_check": self._last_connection_check
        }

# Crear instancia global
ws_manager = WebSocketManager()