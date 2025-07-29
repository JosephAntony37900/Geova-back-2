# HCSR04/infraestructure/ble/hc_ble_reader.py
import asyncio
import json
import time
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
                print(f"🔍 Dispositivo encontrado: {device.name} | {device.address}")
                if device.name == self.device_name:
                    self.device_address = device.address
                    print(f"✅ ESP32 encontrada: {device.name} | {device.address}")
                    return True
                    
            print("❌ No se encontró la ESP32. Verifica que esté encendida.")
            return False
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error en descubrimiento - {e}")
            return False

    def _notification_handler(self, sender, data):
        try:
            raw_data = data.decode('utf-8')
            print(f"📩 Notificación recibida: {raw_data}")
            
            json_data = json.loads(raw_data)
            
            distance = json_data.get('distance')
            
            if distance is not None and distance > 0:
                self.latest_data = {
                    "distancia_cm": float(distance),
                    "timestamp": time.time()
                }
                print(f"📩 HC-SR04 BLE: {distance} cm")
            elif distance is None:
                print("📩 HC-SR04 BLE: Sin lectura del sensor (null)")
            else:
                print(f"📩 HC-SR04 BLE: Distancia inválida: {distance}")
                
        except json.JSONDecodeError as e:
            print(f"🔵 HC-SR04 BLE: Error JSON - {e}")
            print(f"🔍 Datos recibidos (raw): {data}")
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error inesperado - {e}")

    async def connect(self):
        try:
            if not await self.discover_device():
                return False

            if self.client:
                try:
                    if self.client.is_connected:
                        await self.client.disconnect()
                except:
                    pass
                self.client = None

            self.client = BleakClient(self.device_address)
            
            await self.client.connect()
            
            if self.client.is_connected:
                print("🔗 Conectado con la ESP32")
                
                await self.client.start_notify(self.char_uuid, self._notification_handler)
                print("🎧 Escuchando datos BLE...")
                
                self.is_connected = True
                return True
            else:
                print("❌ No se pudo conectar a la ESP32.")
                return False
                
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error de conexión - {e}")
            self.is_connected = False
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
                self.client = None
            return False

    async def disconnect(self):
        try:
            if self.client and self.client.is_connected:
                await self.client.stop_notify(self.char_uuid)
                await self.client.disconnect()
                print("🔵 HC-SR04 BLE: Desconectado")
        except Exception as e:
            print(f"🔵 HC-SR04 BLE: Error al desconectar - {e}")
        finally:
            self.is_connected = False
            self.client = None
            self.latest_data = None

    async def read_async(self) -> dict | None:
        if not self.is_connected:
            if not await self.connect():
                print("🔵 HC-SR04: Sin conexión a la ESP32, sin datos")
                return None
        
        if self.client and not self.client.is_connected:
            print("🔵 HC-SR04: Conexión perdida con ESP32")
            self.is_connected = False
            return None
            
        if self.latest_data:
            current_time = time.time()
            data_age = current_time - self.latest_data.get("timestamp", 0)
            
            if data_age > 5.0:
                print("🔵 HC-SR04: Datos obsoletos, ESP32 podría estar desconectado")
                self.latest_data = None
                return None
            
            return {"distancia_cm": self.latest_data["distancia_cm"]}
        
        return None

    def read(self) -> dict | None:
        """Método sincrónico"""
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