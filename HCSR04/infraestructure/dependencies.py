# HCSR04/infraestructure/dependencies.py
from fastapi import FastAPI
from HCSR04.infraestructure.ble.hc_ble_reader import BLEHCReader
from HCSR04.infraestructure.repositories.hc_repo_mongo import HCSensorRepositoryMongo
from HCSR04.infraestructure.mqtt.publisher import RabbitMQPublisher
from HCSR04.application.hc_usecase import HCUseCase
from HCSR04.infraestructure.controllers.controller_hc import HCController

def init_hc_dependencies(app: FastAPI, engine, rabbitmq_config):
    reader = BLEHCReader(address="ESP32_MAC_ADDR", char_uuid="BLE_CHAR_UUID")
    repo = HCSensorRepositoryMongo(engine)
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key_hc"]
    )
    usecase = HCUseCase(reader, repo, publisher)
    controller = HCController(usecase)
    app.state.hc_controller = controller
