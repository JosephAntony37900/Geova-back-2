# HCSR04/infraestructure/ble/hc_ble_reader.py
import asyncio
import json
from bleak import BleakClient, BleakScanner
from HCSR04.domain.ports.ble_reader import BLEReader

class HCBLEReader(BLEReader):
    def __init__(self, device_name="ESP32_SensorBLE", char_uuid="beb5483e-36e1-4688-b7f5-ea07361b26a8"):
        self.device_name = device_name
        self.char_uuid = char_uuid
        self.device_address = None
        self.client = None
        self.latest_data = None
        self.is_connected = False

    async def discover_device(self):
        try:
            print("🔎 Escaneando dispositivos BLE...")
            devices = await BleakScanner.discover(timeout=10.0)
            
            for device in devices:
                if device.name == self.device_name:
                    self.device_address = device.address
                    print(f"✅ ESP32 encontrada: {device.name} | {device.address}")
                    return True
                    
            print("❌ No se encontró la ESP32. Verifica que esté encendida.")
            return False
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error en descubrimiento - {e}")
            return False

    async def connect(self):
        if not self.device_address:
            if not await self.discover_device():
                return False

        try:
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            
            if self.client.is_connected:
                await self.client.start_notify(self.char_uuid, self._notification_handler)
                self.is_connected = True
                print("🔗 Conectado con ESP32 HC-SR04")
                return True
            else:
                print("❌ No se pudo conectar a la ESP32")
                return False
                
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error de conexión - {e}")
            self.is_connected = False
            return False

    def _notification_handler(self, sender, data):
        try:
            raw_data = data.decode('utf-8')
            print(f"🔍 HC-SR04 BLE datos crudos: {raw_data}")
            
            json_data = json.loads(raw_data)
            
            # Tu ESP32 envía: {"distance": 123.45, "count": 5}
            distance = json_data.get('distance')
            lap_count = json_data.get('count', 0)
            
            if distance is not None and distance > 0:
                self.latest_data = {
                    "distancia_cm": float(distance),
                    "vueltas": int(lap_count)
                }
                print(f"📩 HC-SR04 BLE: {distance} cm | Vueltas: {lap_count}")
            elif distance is None:
                print("📩 HC-SR04 BLE: Sin lectura del sensor (null)")
            else:
                print(f"📩 HC-SR04 BLE: Distancia inválida: {distance}")
                
        except json.JSONDecodeError as e:
            print(f"🔵 HC-SR04 BLE: Error JSON - {e}")
            print(f"🔍 Datos recibidos (raw): {data}")
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error inesperado - {e}")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            try:
                await self.client.stop_notify(self.char_uuid)
                await self.client.disconnect()
                print("🔵 HC-SR04 BLE: Desconectado")
            except Exception as e:
                print(f"🔵 HC-SR04 BLE: Error al desconectar - {e}")
        
        self.is_connected = False
        self.client = None

    async def read_async(self) -> dict | None:
        if not self.is_connected:
            if not await self.connect():
                print("🔵 HC-SR04: Sin conexión a la ESP32, sin datos")
                return None
        
        if self.client and not self.client.is_connected:
            self.is_connected = False
            print("🔵 HC-SR04: Conexión perdida con ESP32")
            return None
            
        if self.latest_data:
            data = self.latest_data.copy()
            return data
        
        return None

    def read(self) -> dict | None:
        try:
            try:
                loop = asyncio.get_running_loop()
                print("⚠️ HC-SR04: read() llamado desde contexto async, usar read_async() en su lugar")
                return None
            except RuntimeError:
                return asyncio.run(self.read_async())
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error en read() - {e}")
            return None