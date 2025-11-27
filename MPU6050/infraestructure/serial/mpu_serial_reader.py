#MPU6050/infraestructure/serial/mpu_serial_reader.py
import time
import math
import platform
import asyncio
from typing import Optional, Dict

IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    import smbus2 as smbus

class MPUSerialReader:
    def __init__(self, bus=1, address=0x68):
        self.address = address
        self.bus_number = bus
        self.bus = None
        self.is_available = False
        self._last_error_time = 0
        self._error_retry_delay = 5  # Segundos entre reintentos tras error
        
        if not IS_WINDOWS:
            self._initialize_bus()
        else:
            print("🧪 Ejecutando en modo simulado (Windows). No se accede al hardware.")
            self.is_available = True  # Simulación disponible

    def _initialize_bus(self) -> bool:
        """Inicializa o reinicializa el bus I2C."""
        try:
            if self.bus is not None:
                try:
                    self.bus.close()
                except:
                    pass
            
            self.bus = smbus.SMBus(self.bus_number)
            # Despertar el MPU6050 (escribir 0 en registro PWR_MGMT_1)
            self.bus.write_byte_data(self.address, 0x6B, 0)
            time.sleep(0.1)  # Esperar a que se estabilice
            self.is_available = True
            print("✅ MPU6050 inicializado correctamente")
            return True
        except OSError as e:
            print(f"⚠️ MPU6050 no disponible (I2C error): {e}")
            self.is_available = False
            return False
        except Exception as e:
            print(f"⚠️ Error inesperado al inicializar MPU6050: {e}")
            self.is_available = False
            return False

    def _read_sync(self) -> Optional[Dict]:
        """Lectura síncrona (ejecutada en thread separado)"""
        if IS_WINDOWS:
            # Datos simulados para pruebas en Windows
            return {
                "ax": 0.01, "ay": 0.02, "az": 0.98,
                "gx": 0.1, "gy": 0.2, "gz": 0.3,
                "roll": 1.5, "pitch": 0.5, "apertura": 2.0
            }
        
        # Si no está disponible, intentar reinicializar después del delay
        if not self.is_available:
            current_time = time.time()
            if current_time - self._last_error_time > self._error_retry_delay:
                print("🔄 MPU6050: Intentando reconectar...")
                if self._initialize_bus():
                    print("✅ MPU6050: Reconexión exitosa")
                else:
                    self._last_error_time = current_time
                    return None
            else:
                return None
        
        if self.bus is None:
            return None

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

        except OSError as e:
            print(f"Error I2C en MPU6050: {e}")
            self.is_available = False
            self._last_error_time = time.time()
            return None
        except Exception as e:
            print(f"Error en MPU6050 al leer datos: {e}")
            return None
    
    async def read(self) -> Optional[Dict]:
        """Lectura async (no bloqueante)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._read_sync)
    
    def read_sync(self) -> Optional[Dict]:
        """DEPRECATED: Usar read() async"""
        return self._read_sync()