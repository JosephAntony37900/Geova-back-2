# TFLuna/infraestructure/ws/ws_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Optional
from core.connectivity import is_connected
import asyncio
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_check_task: Optional[asyncio.Task] = None
        self._check_interval = 5  # segundos entre verificaciones

    async def connect(self, websocket: WebSocket):
        """Maneja la conexión WebSocket con mejor manejo de errores"""
        try:
            await websocket.accept()
            
            # Verificar conexión a internet después de aceptar
            internet_available = await self._check_internet()
            
            if internet_available:
                await self._send_rejection_message(
                    websocket,
                    "El WebSocket solo está disponible cuando no hay conexión a internet"
                )
                return
            
            self.active_connections.append(websocket)
            print(f"🔌 Cliente WebSocket conectado (TF-Luna) - Total: {len(self.active_connections)}")
            
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected",
                "message": "Conexión WebSocket establecida correctamente"
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
        """Envía mensaje de rechazo y cierra la conexión adecuadamente"""
        try:
            await websocket.send_json({
                "type": "connection_status",
                "status": "rejected",
                "message": message,
                "action": "reconnect_when_offline"
            })
            await websocket.close(code=1000, reason=message)  # Código normal de cierre
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
        """Maneja la desconexión del cliente"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 Cliente WebSocket desconectado - Restantes: {len(self.active_connections)}")
            if not self.active_connections and self._connection_check_task:
                self._connection_check_task.cancel()
                self._connection_check_task = None

    async def send_data(self, data: dict):
        """Envía datos a los clientes conectados"""
        if not self.active_connections:
            return

        internet_available = await self._check_internet()
        if internet_available:
            print("🌐 Internet detectado - Cerrando conexiones WebSocket")
            await self._close_all_connections(
                reason="Conexión a internet restablecida",
                code=1000  # Cierre normal
            )
            return

        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except (WebSocketDisconnect, RuntimeError) as e:
                print(f"⚠️ Error enviando datos: {str(e)}")
                disconnected.append(conn)
            except Exception as e:
                print(f"❌ Error inesperado: {str(e)}")
                disconnected.append(conn)

        for conn in disconnected:
            self.disconnect(conn)

    async def _check_internet(self):
        """Verifica el estado de la conexión a internet"""
        return await asyncio.to_thread(is_connected)

    def _start_connection_monitoring(self):
        """Inicia la tarea de monitoreo de conexión si no está activa"""
        if not self._connection_check_task or self._connection_check_task.done():
            self._connection_check_task = asyncio.create_task(self._monitor_connections())

    async def _monitor_connections(self):
        """Monitorea periódicamente el estado de la conexión"""
        while self.active_connections:
            try:
                if await self._check_internet():
                    await self._close_all_connections(
                        reason="Conexión a internet detectada",
                        code=1000  # Cierre normal
                    )
                    break
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                print(f"❌ Error en monitoreo de conexión: {str(e)}")
                break

    async def _close_all_connections(self, reason: str, code: int = 1000):
        """Cierra todas las conexiones con mensaje explicativo"""
        if not self.active_connections:
            return

        print(f"🛑 Cerrando {len(self.active_connections)} conexiones: {reason}")
        
        close_message = json.dumps({
            "type": "connection_status",
            "status": "closing",
            "message": reason,
            "code": code
        })

        for conn in self.active_connections[:]:
            try:
                await conn.send_text(close_message)
                await conn.close(code=code, reason=reason)
            except Exception as e:
                print(f"⚠️ Error al cerrar conexión: {str(e)}")
            finally:
                self.disconnect(conn)

ws_manager = WebSocketManager()