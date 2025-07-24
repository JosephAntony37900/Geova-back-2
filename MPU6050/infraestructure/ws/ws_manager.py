# MPU6050/infraestructure/ws/ws_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

class WebSocketManager_MPU:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔗 Cliente WebSocket conectado (sensor MPU6050) - Total: {len(self.active_connections)} conectado(s)")
        
        # Enviar mensaje de bienvenida
        await self.send_to_connection(websocket, {
            "sensor": "MPU6050",
            "message": "Conectado exitosamente",
            "status": "connected",
            "connections": len(self.active_connections)
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 Cliente WebSocket desconectado (Sensor MPU6050) - Total: {len(self.active_connections)} conectado(s)")

    async def send_to_connection(self, websocket: WebSocket, data: dict):
        """Envía datos a una conexión específica"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"❌ Error enviando datos a conexión específica: {e}")
            # Remover conexión fallida
            self.disconnect(websocket)

    async def send_data(self, data: dict):
        """Envía datos a todas las conexiones activas"""
        if not self.active_connections:
            return
            
        # Lista para conexiones que fallan
        failed_connections = []
        
        for conn in self.active_connections[:]:  # Copia de la lista para evitar modificaciones durante iteración
            try:
                await conn.send_json(data)
            except WebSocketDisconnect:
                failed_connections.append(conn)
            except Exception as e:
                print(f"❌ Error enviando datos por WebSocket: {e}")
                failed_connections.append(conn)
        
        # Remover conexiones fallidas
        for failed_conn in failed_connections:
            self.disconnect(failed_conn)

    async def broadcast_status(self, status: str, message: str = ""):
        """Envía un mensaje de estado a todas las conexiones"""
        await self.send_data({
            "sensor": "MPU6050",
            "status": status,
            "message": message,
            "timestamp": asyncio.get_event_loop().time(),
            "connections": len(self.active_connections)
        })

    def get_connection_count(self) -> int:
        """Retorna el número de conexiones activas"""
        return len(self.active_connections)

# Instancia global
ws_manager_mpu = WebSocketManager_MPU()