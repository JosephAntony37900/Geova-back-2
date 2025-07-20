import time
import math
import platform

IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    import smbus2 as smbus

class MPUSerialReader:
    def __init__(self, bus=1, address=0x68):
        self.address = address
        if not IS_WINDOWS:
            self.bus = smbus.SMBus(bus)
            self.bus.write_byte_data(self.address, 0x6B, 0)
            time.sleep(0.3)  # Esperar a que se estabilice
        else:
            print("🧪 Ejecutando en modo simulado (Windows). No se accede al hardware.")

    def read(self):
        if IS_WINDOWS:
            # Datos simulados para pruebas en Windows
            return {
                "ax": 0.01, "ay": 0.02, "az": 0.98,
                "gx": 0.1, "gy": 0.2, "gz": 0.3,
                "roll": 1.5, "pitch": 0.5, "apertura": 2.0
            }

        def read_word(reg):
            h = self.bus.read_byte_data(self.address, reg)
            l = self.bus.read_byte_data(self.address, reg + 1)
            value = (h << 8) + l
            return value - 65536 if value >= 0x8000 else value

        try:
            ax = read_word(0x3B) / 16384.0
            ay = read_word(0x3D) / 16384.0
            az = read_word(0x3F) / 16384.0
            gx = read_word(0x43) / 131.0
            gy = read_word(0x45) / 131.0
            gz = read_word(0x47) / 131.0

            roll = math.atan2(ay, az) * 57.3
            pitch = math.atan2(-ax, (ay**2 + az**2)**0.5) * 57.3
            apertura = abs(roll) + abs(pitch)

            return {
                "ax": round(ax, 2), "ay": round(ay, 2), "az": round(az, 2),
                "gx": round(gx, 2), "gy": round(gy, 2), "gz": round(gz, 2),
                "roll": round(roll, 2), "pitch": round(pitch, 2),
                "apertura": round(apertura, 2)
            }

        except Exception as e:
            print("❌ Error en MPU6050 al leer datos:", e)
            return None