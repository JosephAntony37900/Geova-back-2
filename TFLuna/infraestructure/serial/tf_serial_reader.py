#TFLuna/infraestructure/serial/tf_serial_reader.py
import serial
import platform

class TFSerialReader:
    def __init__(self, port="/dev/serial10", baudrate=115200):
        if platform.system() != "Windows":
            self.ser = serial.Serial(port, baudrate, timeout=0)
        else:
            self.ser = None
            
    def read(self):
        if self.ser is None or self.ser.in_waiting < 9:
            return None

        data = self.ser.read(9)
        self.ser.reset_input_buffer()

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
