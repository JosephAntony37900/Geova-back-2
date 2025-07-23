# IMX477/infraestructure/streaming/mjpeg_streamer.py
import cv2
import asyncio
import subprocess
import threading
from io import BytesIO
from PIL import Image
import time
import platform

class MJPEGStreamer:
    def __init__(self):
        self.active = False
        self.frame = None
        self.lock = threading.Lock()
        self.fps = 30  # Target FPS
        self.frame_interval = 1.0 / self.fps
        
    def start_streaming(self):
        """Inicia el streaming de la cámara"""
        if self.active:
            return
            
        self.active = True
        # Ejecutar captura en hilo separado para mejor rendimiento
        threading.Thread(target=self._capture_loop, daemon=True).start()
        
    def stop_streaming(self):
        """Detiene el streaming de la cámara"""
        self.active = False
        
    def _capture_loop(self):
        """Loop principal de captura de frames"""
        while self.active:
            start_time = time.time()
            
            try:
                frame = self._capture_frame()
                if frame is not None:
                    with self.lock:
                        self.frame = frame
            except Exception as e:
                print(f"Error capturando frame: {e}")
                
            # Controlar FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_interval - elapsed)
            time.sleep(sleep_time)
    
    def _capture_frame(self):
        """Captura un frame usando libcamera-still"""
        if platform.system() == "Windows":
            # Para testing en Windows, usar webcam
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.resize(frame, (640, 480))
                return frame
            return None
        
        try:
            # Usar libcamera-still para capturar frame en Raspberry Pi
            subprocess.run([
                "libcamera-still", 
                "-n",  # No preview
                "--output", "/dev/shm/streaming_frame.jpg",
                "-t", "50",  # Timeout más corto para mejor FPS
                "--width", "640", 
                "--height", "480",
                "--quality", "85"  # Calidad optimizada
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.2)
            
            frame = cv2.imread("/dev/shm/streaming_frame.jpg")
            return frame
            
        except Exception as e:
            print(f"Error en captura libcamera: {e}")
            return None
    
    def get_current_frame(self):
        """Obtiene el frame actual como JPEG bytes"""
        with self.lock:
            if self.frame is None:
                return None
                
            # Convertir frame a JPEG
            _, buffer = cv2.imencode('.jpg', self.frame, 
                                   [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes()
    
    def is_active(self):
        """Verifica si el streaming está activo"""
        return self.active

# Instancia global del streamer
mjpeg_streamer = MJPEGStreamer()