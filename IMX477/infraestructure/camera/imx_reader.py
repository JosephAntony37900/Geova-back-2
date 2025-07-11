import platform
import cv2
import numpy as np
import subprocess

class IMXReader:
    def obtener_frame(self):
        subprocess.run([
            "libcamera-still", "-n", "--output", "/dev/shm/frame.jpg", "-t", "100",
            "--width", "640", "--height", "480"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return cv2.imread("/dev/shm/frame.jpg")

    def calcular_luminosidad(self, img):
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gris))

    def calcular_nitidez(self, img):
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
        return float(laplaciano.var())

    def detectar_laser(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        rojo_bajo = np.array([0, 100, 100])
        rojo_alto = np.array([10, 255, 255])
        mascara = cv2.inRange(hsv, rojo_bajo, rojo_alto)
        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len(contornos) > 0

    def calcular_score(self, lum, nit, laser):
        lum_score = min(lum / 200, 1.0)
        nit_score = min(nit / 1000, 1.0)
        laser_score = 1.0 if laser else 0.0
        return round((lum_score + nit_score + laser_score) / 3, 2)

    def read(self):
        if platform.system() == "Windows":
            print("📵 No disponible en Windows.")
            return None

        frame = self.obtener_frame()
        if frame is None:
            return None

        lum = self.calcular_luminosidad(frame)
        nit = self.calcular_nitidez(frame)
        laser = self.detectar_laser(frame)
        calidad = self.calcular_score(lum, nit, laser)
        prob = round(calidad * 100, 2)

        return {
            "luminosidad_promedio": round(lum, 2),
            "nitidez_score": round(nit, 2),
            "laser_detectado": laser,
            "calidad_frame": calidad,
            "probabilidad_confiabilidad": prob,
        }
