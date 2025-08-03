# HCSR04/infraestructure/dependencies.py
from fastapi import FastAPI
from HCSR04.infraestructure.ble.hc_ble_reader import HCBLEReader
from HCSR04.infraestructure.mqtt.publisher import RabbitMQPublisher
from HCSR04.application.hc_usecase import HCUseCase
from HCSR04.infraestructure.controllers.controller_hc import HCController
from HCSR04.infraestructure.repositories.hc_repo_dual import DualHCSensorRepository

def init_hc_dependencies(
    app: FastAPI,
    session_local_factory,
    session_remote_factory,
    rabbitmq_config: dict,
    is_connected,
    device_name="ESP32_SensorBLE",
    char_uuid="beb5483e-36e1-4688-b7f5-ea07361b26a8"
):

    reader = HCBLEReader(device_name=device_name, char_uuid=char_uuid)
    repository = DualHCSensorRepository(session_local_factory, session_remote_factory)
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key_hc"]
    )

    usecase = HCUseCase(reader, repository, publisher, is_connected)
    controller = HCController(usecase)
    app.state.hc_controller = controller
    
    print(f"🔵 HC-SR04 BLE configurado: {device_name} | {char_uuid}")