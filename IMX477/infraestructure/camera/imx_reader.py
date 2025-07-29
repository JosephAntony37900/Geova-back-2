# IMX477/infraestructure/camera/imx_reader.py
import platform
import cv2
import numpy as np
import subprocess
import logging

logger = logging.getLogger(__name__)

class IMXReader:
    def obtener_frame(self):
        try:
            result = subprocess.run([
                "rpicam-still", 
                "-n",
                "--output", "/dev/shm/frame.jpg", 
                "-t", "100",
                "--width", "640", 
                "--height", "480",
                "--quality", "90",
                "--encoding", "jpg"
            ], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=5
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
        try:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return float(np.mean(gris))
        except Exception as e:
            logger.error(f"Error calculando luminosidad: {e}")
            return 0.0

    def calcular_nitidez(self, img):
        try:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
            return float(laplaciano.var())
        except Exception as e:
            logger.error(f"Error calculando nitidez: {e}")
            return 0.0

    def detectar_laser(self, img):
        try:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            rojo_bajo = np.array([0, 100, 100])
            rojo_alto = np.array([10, 255, 255])
            mascara1 = cv2.inRange(hsv, rojo_bajo, rojo_alto)
            
            rojo_bajo2 = np.array([160, 100, 100])
            rojo_alto2 = np.array([180, 255, 255])
            mascara2 = cv2.inRange(hsv, rojo_bajo2, rojo_alto2)
            
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
            # Penalizar valores muy bajos o muy altos
            if lum < 50:  # Muy oscuro
                lum_score = lum / 50 * 0.5  # Máximo 0.5 para imágenes muy oscuras
            elif lum > 200:  # Muy brillante (posible sobreexposición)
                lum_score = max(0.3, 1.0 - (lum - 200) / 55 * 0.7)  # Reducir score gradualmente
            else:  # Rango óptimo 50-200
                lum_score = 0.5 + (lum - 50) / 150 * 0.5  # Score entre 0.5 y 1.0
            
            # Normalizar nitidez con curva más realista
            # Valores típicos: 0-100 (muy borroso), 100-500 (aceptable), 500+ (nítido)
            if nit < 100:
                nit_score = nit / 100 * 0.3  # Máximo 0.3 para imágenes muy borrosas
            elif nit < 500:
                nit_score = 0.3 + (nit - 100) / 400 * 0.5  # Score entre 0.3 y 0.8
            else:
                nit_score = min(1.0, 0.8 + (nit - 500) / 1000 * 0.2)  # Score entre 0.8 y 1.0
            
            # Score de detección de láser
            laser_score = 1.0 if laser else 0.0
            
            # Cálculo de probabilidad de confiabilidad más sofisticado
            # Consideramos la combinación de factores
            base_score = (lum_score * 0.35 + nit_score * 0.45 + laser_score * 0.20)
            
            # Bonus por combinaciones ideales
            bonus = 0.0
            if laser and lum_score > 0.7 and nit_score > 0.7:
                bonus = 0.1  # Bonus por condiciones ideales
            elif laser and (lum_score > 0.5 or nit_score > 0.5):
                bonus = 0.05  # Bonus menor por condiciones parcialmente buenas
            
            # Penalización por combinaciones problemáticas
            penalty = 0.0
            if lum_score < 0.3 and nit_score < 0.3:
                penalty = 0.2  # Penalización fuerte por imagen muy mala
            elif lum_score < 0.5 and nit_score < 0.5 and not laser:
                penalty = 0.1  # Penalización por condiciones generalmente malas
            
            # Score final
            final_score = max(0.0, min(1.0, base_score + bonus - penalty))
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculando score: {e}")
            return 0.0

    def calcular_probabilidad_confiabilidad(self, lum, nit, laser, calidad_base):
        """
        Calcula la probabilidad de confiabilidad considerando todos los factores.
        """
        try:
            # Factor de luminosidad (0-1)
            if 80 <= lum <= 180:  # Rango óptimo
                factor_lum = 1.0
            elif 50 <= lum <= 200:  # Rango aceptable
                factor_lum = 0.8
            elif lum < 30 or lum > 230:  # Muy malo
                factor_lum = 0.2
            else:  # Regular
                factor_lum = 0.5
            
            # Factor de nitidez (0-1)
            if nit >= 800:  # Muy nítido
                factor_nit = 1.0
            elif nit >= 400:  # Nítido
                factor_nit = 0.8
            elif nit >= 150:  # Aceptable
                factor_nit = 0.6
            elif nit >= 50:  # Regular
                factor_nit = 0.3
            else:  # Borroso
                factor_nit = 0.1
            
            # Factor de detección de láser
            factor_laser = 1.2 if laser else 0.8
            
            # Factor de consistencia (qué tan bien coinciden los valores)
            consistencia = 1.0
            if (factor_lum > 0.7 and factor_nit < 0.3) or (factor_lum < 0.3 and factor_nit > 0.7):
                consistencia = 0.7  # Penalizar inconsistencias
            
            # Cálculo final
            probabilidad_base = (factor_lum * 0.3 + factor_nit * 0.4) * factor_laser * consistencia
            
            # Incorporar la calidad del frame como factor adicional
            probabilidad_final = (probabilidad_base * 0.7 + calidad_base * 0.3)
            
            # Asegurar que esté en el rango 0-100
            probabilidad_final = max(0, min(100, probabilidad_final * 100))
            
            return round(probabilidad_final, 2)
            
        except Exception as e:
            logger.error(f"Error calculando probabilidad de confiabilidad: {e}")
            return 0.0

    def read(self):
        if platform.system() == "Windows":
            logger.warning("📵 IMX477 no disponible en Windows.")
            return None

        try:
            frame = self.obtener_frame()
            if frame is None:
                logger.error("No se pudo obtener frame de la cámara")
                return None

            # Calcular métricas
            lum = self.calcular_luminosidad(frame)
            nit = self.calcular_nitidez(frame)
            laser = self.detectar_laser(frame)
            calidad = self.calcular_score(lum, nit, laser)
            
            # Calcular probabilidad de confiabilidad basada en todos los factores
            prob = self.calcular_probabilidad_confiabilidad(lum, nit, laser, calidad)

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