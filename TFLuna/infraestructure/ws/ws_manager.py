# TFLuna/infraestructure/ws/ws_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from core.connectivity import is_connected
import asyncio
import json
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_check_task: Optional[asyncio.Task] = None
        self._check_interval = 5
        self._data_queue: List[Dict[str, Any]] = []
        self._max_queue_size = 100  # Límite de datos en cola

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            
            internet_available = await self._check_internet()
            
            if internet_available:
                await self._send_rejection_message(
                    websocket,
                    "El WebSocket solo está disponible cuando no hay conexión a internet"
                )
                return
            
            self.active_connections.append(websocket)
            print(f"🔌 Cliente WebSocket conectado (TF-Luna) - Total: {len(self.active_connections)}")
            
            # Enviar datos en cola al nuevo cliente
            if self._data_queue:
                await self._send_queued_data(websocket)
            
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected",
                "message": "Conexión WebSocket establecida correctamente",
                "queued_data_count": len(self._data_queue)
            })
            
            self._start_connection_monitoring()
            
        except Exception as e:
            print(f"❌ Error durante la conexión WebSocket: {str(e)}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except:
                pass

    async def _send_rejection_message(self, websocket: WebSocket, message: str):
        try:
            await websocket.send_json({
                "type": "connection_status",
                "status": "rejected",
                "message": message,
                "action": "reconnect_when_offline"
            })
            await websocket.close(code=1000, reason=message)
        except Exception as e:
            print(f"❌ Error al enviar mensaje de rechazo: {str(e)}")
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
            print(f"🔌 Cliente WebSocket desconectado - Restantes: {len(self.active_connections)}")
            if not self.active_connections and self._connection_check_task:
                self._connection_check_task.cancel()
                self._connection_check_task = None

    async def send_data(self, data: dict):
        """
        Envía datos del sensor TF-Luna via WebSocket cuando no hay internet.
        Actúa como alternativa a RabbitMQ.
        """
        internet_available = await self._check_internet()
        
        if internet_available:
            print("🌐 Internet detectado - Cerrando conexiones WebSocket")
            await self._close_all_connections(
                reason="Conexión a internet restablecida",
                code=1000
            )
            return False  # Indica que no se envió por WebSocket

        # Añadir timestamp y metadata
        enriched_data = {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "tfluna_sensor",
            "connection_type": "websocket_offline",
            "data_type": "sensor_reading"
        }

        # Si no hay conexiones activas, almacenar en cola
        if not self.active_connections:
            self._queue_data(enriched_data)
            print(f"📦 Datos TF-Luna almacenados en cola (total: {len(self._data_queue)})")
            return True

        # Enviar a todas las conexiones activas
        disconnected = []
        sent_count = 0
        
        for conn in self.active_connections:
            try:
                await conn.send_json({
                    "type": "sensor_data",
                    "sensor": "tfluna",
                    "data": enriched_data
                })
                sent_count += 1
            except (WebSocketDisconnect, RuntimeError) as e:
                print(f"⚠️ Error enviando datos TF-Luna: {str(e)}")
                disconnected.append(conn)
            except Exception as e:
                print(f"❌ Error inesperado enviando TF-Luna: {str(e)}")
                disconnected.append(conn)

        # Limpiar conexiones desconectadas
        for conn in disconnected:
            self.disconnect(conn)

        if sent_count > 0:
            print(f"📡 Datos TF-Luna enviados a {sent_count} cliente(s) WebSocket")
        
        return True  # Indica que se procesó correctamente

    async def send_as_rabbitmq_alternative(self, data: dict, routing_key: str = "tfluna.data"):
        """
        Método específico para actuar como alternativa a RabbitMQ
        """
        rabbitmq_style_data = {
            "routing_key": routing_key,
            "exchange": "sensors",
            "body": data,
            "timestamp": datetime.utcnow().isoformat(),
            "delivery_mode": "websocket_offline",
            "correlation_id": f"tfluna_{datetime.utcnow().timestamp()}"
        }
        
        return await self.send_data(rabbitmq_style_data)

    def _queue_data(self, data: dict):
        """Almacena datos cuando no hay conexiones WebSocket activas"""
        self._data_queue.append(data)
        
        # Mantener solo los datos más recientes
        if len(self._data_queue) > self._max_queue_size:
            removed = self._data_queue.pop(0)
            print(f"📦 Cola llena, removiendo dato más antiguo: {removed.get('timestamp', 'N/A')}")

    async def _send_queued_data(self, websocket: WebSocket):
        """Envía datos en cola a una nueva conexión"""
        try:
            if self._data_queue:
                await websocket.send_json({
                    "type": "queued_data",
                    "sensor": "tfluna",
                    "data": self._data_queue.copy(),
                    "count": len(self._data_queue)
                })
                print(f"📦 Enviados {len(self._data_queue)} datos en cola al nuevo cliente")
        except Exception as e:
            print(f"❌ Error enviando datos en cola: {str(e)}")

    async def clear_queue(self):
        """Limpia la cola de datos almacenados"""
        cleared_count = len(self._data_queue)
        self._data_queue.clear()
        print(f"🗑️ Cola de datos TF-Luna limpiada ({cleared_count} elementos)")
        return cleared_count

    async def get_queue_status(self) -> dict:
        """Retorna el estado de la cola de datos"""
        return {
            "queue_size": len(self._data_queue),
            "max_queue_size": self._max_queue_size,
            "active_connections": len(self.active_connections),
            "oldest_data": self._data_queue[0].get('timestamp') if self._data_queue else None,
            "newest_data": self._data_queue[-1].get('timestamp') if self._data_queue else None
        }

    async def _check_internet(self):
        return await asyncio.to_thread(is_connected)

    def _start_connection_monitoring(self):
        if not self._connection_check_task or self._connection_check_task.done():
            self._connection_check_task = asyncio.create_task(self._monitor_connections())

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
                print(f"❌ Error en monitoreo de conexión: {str(e)}")
                break

    async def _close_all_connections(self, reason: str, code: int = 1000):
        if not self.active_connections:
            return

        print(f"🛑 Cerrando {len(self.active_connections)} conexiones: {reason}")
        
        close_message = json.dumps({
            "type": "connection_status",
            "status": "closing",
            "message": reason,
            "code": code,
            "queued_data_count": len(self._data_queue)
        })

        for conn in self.active_connections[:]:
            try:
                await conn.send_text(close_message)
                await conn.close(code=code, reason=reason)
            except Exception as e:
                print(f"⚠️ Error al cerrar conexión: {str(e)}")
            finally:
                self.disconnect(conn)

# Instancia global
ws_manager = WebSocketManager()