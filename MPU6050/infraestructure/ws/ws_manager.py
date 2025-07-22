# MPU6050/infraestructure/ws/ws_manager.py
from fastapi import WebSocket
from typing import List

class WebSocketManager_MPU:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Cliente WebSocket conectado (sensor MPU6050)({len(self.active_connections)} conectado(s))")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Cliente WebSocket desconectado (Sensor MPU6050)")

    async def send_data(self, data: dict):
        for conn in self.active_connections:
            try:
                await conn.send_json(data)
            except Exception as e:
                print("Error enviando datos por WebSocket:", e)
ws_manager_mpu = WebSocketManager_MPU()