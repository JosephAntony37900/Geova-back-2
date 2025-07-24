# IMX477/infraestructure/camera/imx_reader.py
import platform
import cv2
import numpy as np
import subprocess
import logging

logger = logging.getLogger(__name__)

class IMXReader:
    def obtener_frame(self):
        """Captura un frame usando rpicam-still en lugar de libcamera-still."""
        try:
            # Cambio de libcamera-still a rpicam-still
            result = subprocess.run([
                "rpicam-still", 
                "-n",  # No preview
                "--output", "/dev/shm/frame.jpg", 
                "-t", "100",  # Timeout 100ms
                "--width", "640", 
                "--height", "480",
                "--quality", "90",  # Calidad JPEG
                "--encoding", "jpg"  # Asegurar encoding JPEG
            ], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=5  # Timeout de 5 segundos
            )
            
            if result.returncode != 0:
                logger.error(f"rpicam-still falló con código: {result.returncode}")
                return None
                
            frame = cv2.imread("/dev/shm/frame.jpg")
            if frame is None:
                logger.error("No se pudo leer el frame capturado")
                
            return frame
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout al capturar frame con rpicam-still")
            return None
        except Exception as e:
            logger.error(f"Error al capturar frame: {e}")
            return None

    def calcular_luminosidad(self, img):
        """Calcula la luminosidad promedio del frame."""
        try:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return float(np.mean(gris))
        except Exception as e:
            logger.error(f"Error calculando luminosidad: {e}")
            return 0.0

    def calcular_nitidez(self, img):
        """Calcula la nitidez usando el operador Laplaciano."""
        try:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
            return float(laplaciano.var())
        except Exception as e:
            logger.error(f"Error calculando nitidez: {e}")
            return 0.0

    def detectar_laser(self, img):
        """Detecta si hay un láser rojo en la imagen."""
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Rango para detectar rojo en HSV
            rojo_bajo = np.array([0, 100, 100])
            rojo_alto = np.array([10, 255, 255])
            mascara1 = cv2.inRange(hsv, rojo_bajo, rojo_alto)
            
            # Segundo rango para rojo (que está en el otro extremo del espectro HSV)
            rojo_bajo2 = np.array([160, 100, 100])
            rojo_alto2 = np.array([180, 255, 255])
            mascara2 = cv2.inRange(hsv, rojo_bajo2, rojo_alto2)
            
            # Combinar ambas máscaras
            mascara = mascara1 + mascara2
            
            contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtrar contornos por área mínima para evitar ruido
            contornos_validos = [c for c in contornos if cv2.contourArea(c) > 10]
            
            return len(contornos_validos) > 0
            
        except Exception as e:
            logger.error(f"Error detectando láser: {e}")
            return False

    def calcular_score(self, lum, nit, laser):
        """Calcula un score de calidad basado en luminosidad, nitidez y detección de láser."""
        try:
            # Normalizar luminosidad (0-255 -> 0-1)
            lum_score = min(lum / 200, 1.0)
            
            # Normalizar nitidez (valores típicos 0-2000 -> 0-1)
            nit_score = min(nit / 1000, 1.0)
            
            # Bonus por detección de láser
            laser_score = 1.0 if laser else 0.0
            
            # Promedio ponderado
            score = (lum_score * 0.4 + nit_score * 0.4 + laser_score * 0.2)
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error calculando score: {e}")
            return 0.0

    def read(self):
        """Lee datos del sensor IMX477."""
        if platform.system() == "Windows":
            logger.warning("📵 IMX477 no disponible en Windows.")
            return None

        try:
            # Capturar frame
            frame = self.obtener_frame()
            if frame is None:
                logger.error("No se pudo obtener frame de la cámara")
                return None

            # Calcular métricas
            lum = self.calcular_luminosidad(frame)
            nit = self.calcular_nitidez(frame)
            laser = self.detectar_laser(frame)
            calidad = self.calcular_score(lum, nit, laser)
            prob = round(calidad * 100, 2)

            datos = {
                "luminosidad_promedio": round(lum, 2),
                "nitidez_score": round(nit, 2),
                "laser_detectado": laser,
                "calidad_frame": calidad,
                "probabilidad_confiabilidad": prob,
            }
            
            logger.debug(f"Datos IMX477: {datos}")
            return datos
            
        except Exception as e:
            logger.error(f"Error leyendo datos IMX477: {e}")
            return None