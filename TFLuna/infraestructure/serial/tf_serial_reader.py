#TFLuna/infraestructure/serial/tf_serial_reader.py
import serial
import platform

class TFSerialReader:
    def __init__(self, port="/dev/ttyAMA0", baudrate=115200):
        self.ser = None
        self.is_available = False
        
        if platform.system() != "Windows":
            try:
                self.ser = serial.Serial(port, baudrate, timeout=0)
                self.is_available = True
                print("✅ TFLuna inicializado correctamente")
            except serial.SerialException as e:
                print(f"⚠️ TFLuna no disponible (Serial error): {e}")
                print("   El sensor TFLuna no está conectado o el puerto no existe.")
                print("   La aplicación continuará sin el sensor TFLuna.")
                self.is_available = False
            except Exception as e:
                print(f"⚠️ Error inesperado al inicializar TFLuna: {e}")
                self.is_available = False
        else:
            print("🧪 TFLuna: Ejecutando en modo simulado (Windows).")
            
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
