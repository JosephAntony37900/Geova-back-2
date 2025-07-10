# --- src/controllers/sensorTF_controller.py ---
import time
import platform
from src.models.sensorTF_model import SensorTF
from odmantic import AIOEngine
from src.rabbitmq.publisher import publish_data
from config import ROUTING_KEY_TF  # <- importa la routing key desde .env/config

# --- Inicializar puerto serial solo si no es Windows ---
try:
    import serial
    if platform.system() != "Windows":
        BAUDRATE = 115200
        PORT = "/dev/serial0"
        ser = serial.Serial(PORT, BAUDRATE, timeout=0)
    else:
        ser = None
except Exception as e:
    print("⚠️ Error al inicializar el puerto serial:", e)
    ser = None

# --- Leer datos del sensor TF-Luna ---
def read_sensor():
    if ser is None:
        print("⚠️ Sensor deshabilitado (no se detectó puerto serial).")
        return None

    if ser.in_waiting >= 9:
        data = ser.read(9)
        ser.reset_input_buffer()

        if data[0] == 0x59 and data[1] == 0x59:
            distance = data[2] + data[3] * 256
            strength = data[4] + data[5] * 256
            temperature = (data[6] + data[7] * 256) / 8 - 256

            if distance >= 20:
                meters = round(distance / 100, 2)
                return {
                    "distancia_cm": distance,
                    "distancia_m": meters,
                    "fuerza_senal": strength,
                    "temperatura": round(temperature, 2)
                }
    return None


# --- Guardar en MongoDB y enviar a RabbitMQ ---
async def read_and_store(engine: AIOEngine, event: bool = False):
    sensor_raw = read_sensor()

    if sensor_raw is None:
        print("⛔ No se obtuvo lectura válida del sensor.")
        return None

    sensor_data = SensorTF(
        id_project=1,
        event=event,  # ← aplicar flag
        **sensor_raw
    )

    # Publicar SIEMPRE
    try:
        publish_data(sensor_data, ROUTING_KEY_TF)
    except Exception as e:
        print("❌ Error al enviar a RabbitMQ:", e)

    # Guardar solo si event=True
    if event:
        await engine.save(sensor_data)

    return sensor_data

