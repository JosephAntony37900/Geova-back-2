# --- src/controllers/sensorIMX477_controller.py ---
import platform
import cv2
import numpy as np
import subprocess
from datetime import datetime
from odmantic import AIOEngine
from src.models.sensorIMX477_model import SensorIMX477
from src.rabbitmq.publisher import publish_data
from config import ROUTING_KEY_IMX477

def obtener_frame():
    subprocess.run([
        "libcamera-still", "-n", "--output", "/dev/shm/frame.jpg", "-t", "100",
        "--width", "640", "--height", "480"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return cv2.imread("/dev/shm/frame.jpg")

def calcular_luminosidad(img):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gris))

def calcular_nitidez(img):
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplaciano = cv2.Laplacian(gris, cv2.CV_64F)
    varianza = laplaciano.var()
    return float(varianza)

def detectar_laser(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    rojo_bajo = np.array([0, 100, 100])
    rojo_alto = np.array([10, 255, 255])
    mascara = cv2.inRange(hsv, rojo_bajo, rojo_alto)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contornos) > 0

def calcular_score(lum, nit, laser):
    lum_score = min(lum / 200, 1.0)
    nit_score = min(nit / 1000, 1.0)
    laser_score = 1.0 if laser else 0.0
    return round((lum_score + nit_score + laser_score) / 3, 2)

async def analizar_frame(engine: AIOEngine, id_project: int = 1, resolution: str = "640x480", event: bool = False):
    if platform.system() == "Windows":
        print("📵 No disponible en Windows.")
        return None

    frame = obtener_frame()
    if frame is None:
        print("❌ No se pudo capturar frame.")
        return None

    lum = calcular_luminosidad(frame)
    nit = calcular_nitidez(frame)
    laser = detectar_laser(frame)
    calidad = calcular_score(lum, nit, laser)
    probabilidad = round(calidad * 100, 2)

    datos = SensorIMX477(
        id_project=id_project,
        resolution=resolution,
        luminosidad_promedio=round(lum, 2),
        nitidez_score=round(nit, 2),
        laser_detectado=laser,
        calidad_frame=calidad,
        probabilidad_confiabilidad=probabilidad,
        event=event  # ← aplicar flag
    )

    # Publicar SIEMPRE
    try:
        publish_data(datos, ROUTING_KEY_IMX477)
    except Exception as e:
        print("❌ Error al enviar a RabbitMQ:", e)

    # Guardar solo si event=True
    if event:
        await engine.save(datos)

    return datos

