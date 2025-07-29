# TFLuna/infraestructure/ws/ws_manager.py (Versión mejorada)
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
from core.connectivity import is_connected
import asyncio
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_check_task: Optional[asyncio.Task] = None
        self._check_interval = 5
        self._message_count = 0  # Contador de mensajes enviados

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            logger.info("🔌 WebSocket connection attempt")
            
            internet_available = await self._check_internet()
            logger.info(f"🌐 Internet status: {'Available' if internet_available else 'Offline'}")
            
            if internet_available:
                await self._send_rejection_message(
                    websocket,
                    "El WebSocket solo está disponible cuando no hay conexión a internet"
                )
                return
            
            self.active_connections.append(websocket)
            logger.info(f"✅ Cliente WebSocket conectado (TF-Luna) - Total: {len(self.active_connections)}")
            
            # Enviar mensaje de bienvenida mejorado
            welcome_message = {
                "type": "connection_status",
                "status": "connected",
                "message": "Conexión WebSocket establecida correctamente",
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_type": "TF-Luna",
                "debug": True
            }
            await websocket.send_json(welcome_message)
            logger.info(f"📤 Mensaje de bienvenida enviado: {welcome_message}")
            
            # Enviar mensaje de prueba cada 5 segundos
            asyncio.create_task(self._send_test_messages(websocket))
            
            self._start_connection_monitoring()
            
        except Exception as e:
            logger.error(f"❌ Error durante la conexión WebSocket: {str(e)}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except:
                pass

    async def _send_test_messages(self, websocket: WebSocket):
        """Envía mensajes de prueba cada 5 segundos para verificar conectividad"""
        counter = 0
        while websocket in self.active_connections:
            try:
                test_message = {
                    "type": "test_message",
                    "counter": counter,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Mensaje de prueba #{counter}"
                }
                await websocket.send_json(test_message)
                logger.info(f"🧪 Mensaje de prueba enviado: #{counter}")
                counter += 1
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Error enviando mensaje de prueba: {e}")
                break

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
        finally:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔌 Cliente WebSocket desconectado - Restantes: {len(self.active_connections)}")
            if not self.active_connections and self._connection_check_task:
                self._connection_check_task.cancel()
                self._connection_check_task = None

    async def send_data(self, data: dict):
        if not self.active_connections:
            logger.warning("⚠️ No hay conexiones WebSocket activas")
            return

        internet_available = await self._check_internet()
        if internet_available:
            logger.info("🌐 Internet detectado - Cerrando conexiones WebSocket")
            await self._close_all_connections(
                reason="Conexión a internet restablecida",
                code=1000
            )
            return

        # Agregar metadata al mensaje
        enhanced_data = {
            **data,
            "message_id": self._message_count,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "sensor_data",
            "sensor_type": "TF-Luna"
        }
        
        self._message_count += 1
        logger.info(f"📤 Enviando datos a {len(self.active_connections)} conexiones: {enhanced_data}")

        disconnected = []
        for i, conn in enumerate(self.active_connections):
            try:
                await conn.send_json(enhanced_data)
                logger.info(f"✅ Datos enviados a conexión #{i}")
            except (WebSocketDisconnect, RuntimeError) as e:
                logger.warning(f"⚠️ Error enviando datos a conexión #{i}: {str(e)}")
                disconnected.append(conn)
            except Exception as e:
                logger.error(f"❌ Error inesperado en conexión #{i}: {str(e)}")
                disconnected.append(conn)

        for conn in disconnected:
            self.disconnect(conn)
            
        logger.info(f"📊 Resumen: {len(self.active_connections)} conexiones activas, {len(disconnected)} desconectadas")

    async def _check_internet(self):
        try:
            result = await asyncio.to_thread(is_connected)
            logger.debug(f"🌐 Check internet result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error checking internet: {e}")
            return False

    def _start_connection_monitoring(self):
        if not self._connection_check_task or self._connection_check_task.done():
            self._connection_check_task = asyncio.create_task(self._monitor_connections())
            logger.info("🔍 Monitoreo de conexiones iniciado")

    async def _monitor_connections(self):
        while self.active_connections:
            try:
                if await self._check_internet():
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
                self.disconnect(conn)

    def get_stats(self):
        """Obtener estadísticas del WebSocket"""
        return {
            "active_connections": len(self.active_connections),
            "messages_sent": self._message_count,
            "monitoring_active": self._connection_check_task is not None and not self._connection_check_task.done()
        }

ws_manager = WebSocketManager()