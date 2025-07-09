# --- controllers/sensorTF_controller.py ---
import serial
import time
from src.models.sensorTF_model import SensorTF
from odmantic import AIOEngine
from src.rabbitmq.publisher import publish_data

BAUDRATE = 115200
PORT = "/dev/serial0"
ser = serial.Serial(PORT, BAUDRATE, timeout=0)

def read_sensor():
    if ser.in_waiting >= 9:
        data = ser.read(9)
        ser.reset_input_buffer()

        if data[0] == 0x59 and data[1] == 0x59:
            distance = data[2] + data[3] * 256
            strength = data[4] + data[5] * 256
            temperature = (data[6] + data[7] * 256) / 8 - 256

            if distance >= 20:
                meters = round(distance / 100, 2)
                return SensorTF(
                    distancia_cm=distance,
                    distancia_m=meters,
                    fuerza_senal=strength,
                    temperatura=round(temperature, 2)
                )
    return None

async def read_and_store(engine: AIOEngine):
    sensor_data = SensorTF(
        distancia_cm=100,
        distancia_m=1.0,
        fuerza_senal=200,
        temperatura=25.0
    )
    await engine.save(sensor_data)
    publish_data(sensor_data)
    return sensor_data


#async def read_and_store(engine: AIOEngine):
 #   sensor_data = read_sensor()
 #   if sensor_data:
   #     await engine.save(sensor_data)
   #     publish_data(sensor_data)
  #  return sensor_data