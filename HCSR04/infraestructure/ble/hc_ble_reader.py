# HCSR04/infraestructure/ble/hc_ble_reader.py
import asyncio
from bleak import BleakClient

class BLEHCReader:
    def __init__(self, address, char_uuid):
        self.address = address
        self.char_uuid = char_uuid

    def read(self):
        """Lectura síncrona simulada desde BLE"""
        data = asyncio.run(self._read_ble())
        if data:
            return {"distancia_cm": float(data)}
        return None

    async def _read_ble(self):
        try:
            async with BleakClient(self.address) as client:
                if await client.is_connected():
                    data = await client.read_gatt_char(self.char_uuid)
                    return data.decode("utf-8")
        except Exception as e:
            print(f"Error BLE: {e}")
        return None
