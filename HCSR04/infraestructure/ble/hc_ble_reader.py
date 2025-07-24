# HCSR04/infraestructure/ble/hc_ble_reader.py
import asyncio
import platform
from bleak import BleakClient
from HCSR04.domain.ports.ble_reader import BLEReader

class HCBLEReader(BLEReader):
    def __init__(self, address="00:11:22:33:44:55", char_uuid="0000ffe1-0000-1000-8000-00805f9b34fb"):
        self.address = address
        self.char_uuid = char_uuid
        
        # Simulación para Windows
        if platform.system() == "Windows":
            print("🧪 Ejecutando en modo simulado (Windows). No se accede al hardware BLE.")
            self.is_simulation = True
        else:
            self.is_simulation = False

    async def read_async(self) -> dict | None:
        """Lectura asíncrona desde BLE"""
        if self.is_simulation:
            # En Windows, simular que no hay conexión BLE
            print("🔵 HC-SR04 BLE: Sin conexión BLE (simulación)")
            return None
        
        try:
            data = await self._read_ble()
            if data:
                try:
                    distance = float(data)
                    return {"distancia_cm": distance}
                except ValueError:
                    print(f"🔵 HC-SR04 BLE: Error al convertir datos: {data}")
                    return None
            return None
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error de conexión - {e}")
            return None

    def read(self) -> dict | None:
        """Método síncrono mantenido para compatibilidad"""
        # ⚠️ ADVERTENCIA: Este método no debe usarse desde contextos async
        # Solo se mantiene para compatibilidad hacia atrás
        if self.is_simulation:
            return None
        
        try:
            # Verificar si ya estamos en un event loop
            try:
                loop = asyncio.get_running_loop()
                print("⚠️ HC-SR04: read() llamado desde contexto async, usar read_async() en su lugar")
                return None
            except RuntimeError:
                # No hay event loop, podemos usar asyncio.run
                data = asyncio.run(self._read_ble())
                if data:
                    try:
                        distance = float(data)
                        return {"distancia_cm": distance}
                    except ValueError:
                        print(f"🔵 HC-SR04 BLE: Error al convertir datos: {data}")
                        return None
                return None
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error de conexión - {e}")
            return None

    async def _read_ble(self) -> str | None:
        """Lectura interna BLE"""
        try:
            async with BleakClient(self.address) as client:
                if await client.is_connected():
                    data = await client.read_gatt_char(self.char_uuid)
                    return data.decode("utf-8").strip()
                else:
                    print("🔵 HC-SR04 BLE: No se pudo conectar al dispositivo")
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error de conexión - {e}")
        return None