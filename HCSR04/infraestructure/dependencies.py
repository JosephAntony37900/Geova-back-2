# HCSR04/infraestructure/dependencies.py
import platform
from fastapi import FastAPI
from HCSR04.infraestructure.ble.hc_ble_reader import HCBLEReader
from HCSR04.infraestructure.repositories.hc_repo_mongo import MongoHCSensorRepository
from HCSR04.infraestructure.mqtt.publisher import  MQTTPublisherHC
from HCSR04.application.hc_usecase import HCUseCase
from HCSR04.infraestructure.controllers.controller_hc import HCController

def init_hc_dependencies(app: FastAPI, engine, rabbitmq_config):
    # Dirección y UUID reales para ESP32
    ble_address = "00:11:22:33:44:55"  # ← REEMPLAZAR con la dirección MAC real del ESP32
    char_uuid = "0000ffe1-0000-1000-8000-00805f9b34fb"  # ← REEMPLAZAR con el UUID real del servicio

    if platform.system() == "Windows":
        print("🧪 Ejecutando en modo simulado (Windows). No se accede al hardware.")
        # Puedes usar valores falsos o simular el BLEReader
        reader = HCBLEReader("00:00:00:00:00:00", "00000000-0000-0000-0000-000000000000")
    else:
        reader = HCBLEReader(address=ble_address, char_uuid=char_uuid)

    repo = MongoHCSensorRepository(engine)

    publisher = MQTTPublisherHC(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key_hc"]
    )

    usecase = HCUseCase(reader, repo, publisher)
    controller = HCController(usecase)
    app.state.hc_controller = controller
