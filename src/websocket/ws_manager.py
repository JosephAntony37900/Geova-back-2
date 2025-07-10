from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
      disconnected = []
      for connection in self.active_connections:
            try:
                  await connection.send_json(message)
            except Exception:
                  disconnected.append(connection)

      for conn in disconnected:
            self.active_connections.remove(conn)

