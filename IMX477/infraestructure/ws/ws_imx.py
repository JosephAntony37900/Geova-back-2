import cv2
import base64
import asyncio
from fastapi import WebSocket
from threading import Thread

class VideoStreamer:
    def __init__(self):
        self.clients = []
        self.capture = cv2.VideoCapture(0)  

    def register(self, websocket: WebSocket):
        self.clients.append(websocket)

    def unregister(self, websocket: WebSocket):
        self.clients.remove(websocket)

    async def send_frames(self):
        while True:
            ret, frame = self.capture.read()
            if not ret:
                continue

            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            for ws in self.clients:
                try:
                    await ws.send_text(jpg_as_text)
                except:
                    self.clients.remove(ws)

            await asyncio.sleep(0.05)  # ~20 FPS
