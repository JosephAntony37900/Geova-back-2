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

    def read(self) -> dict:
        """Lectura síncrona desde BLE"""
        if self.is_simulation:
            # Datos simulados para Windows
            return {"distancia_cm": 25.5}
        
        data = asyncio.run(self._read_ble())
        if data:
            try:
                distance = float(data)
                return {"distancia_cm": distance}
            except ValueError:
                print(f"Error al convertir datos BLE: {data}")
                return None
        return None

    async def _read_ble(self) -> str | None:
        try:
            async with BleakClient(self.address) as client:
                if await client.is_connected():
                    data = await client.read_gatt_char(self.char_uuid)
                    return data.decode("utf-8").strip()
        except Exception as e:
            print(f"Error BLE HC-SR04: {e}")
        return None