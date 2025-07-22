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
    ble_address="00:11:22:33:44:55",
    char_uuid="0000ffe1-0000-1000-8000-00805f9b34fb"
):
    reader = HCBLEReader(address=ble_address, char_uuid=char_uuid)
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