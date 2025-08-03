import asyncio
from bleak import BleakClient, BleakScanner

CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DEVICE_NAME = "ESP32_SensorBLE"

def notification_handler(sender, data):
    print(f"📩 Notificación recibida: {data.decode('utf-8')}")

async def main():
    print("🔎 Escaneando dispositivos BLE...")
    devices = await BleakScanner.discover()

    esp32_address = None
    for d in devices:
        if d.name == DEVICE_NAME:
            esp32_address = d.address
            print(f"✅ ESP32 encontrada: {d.name} | {d.address}")
            break

    if esp32_address is None:
        print("❌ No se encontró la ESP32. Asegúrate de que esté encendida y emitiendo BLE.")
        return

    client = BleakClient(esp32_address)

    try:
        await client.connect()
        if client.is_connected:
            print("🔗 Conectado con la ESP32")
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            print("🎧 Escuchando datos BLE... Ctrl+C para salir")

            while True:
                await asyncio.sleep(1)
        else:
            print("❌ No se pudo conectar a la ESP32.")
    except asyncio.CancelledError:
        print("🛑 Cancelación detectada")
    except KeyboardInterrupt:
        print("🧹 Interrupción por teclado. Cerrando cliente BLE...")
    finally:
        if client.is_connected:
            await client.disconnect()
        print("✅ Cliente cerrado con éxito")

asyncio.run(main())