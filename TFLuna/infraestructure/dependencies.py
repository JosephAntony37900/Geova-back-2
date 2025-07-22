from fastapi import FastAPI
from TFLuna.infraestructure.serial.tf_serial_reader import TFSerialReader
from TFLuna.infraestructure.mqtt.publisher import RabbitMQPublisher
from TFLuna.application.tf_usecases import TFUseCase
from TFLuna.infraestructure.controllers.controller_tf import TFController
from TFLuna.infraestructure.repositories.tf_repo_dual import DualTFLunaRepository
import aiohttp

async def is_connected() -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com", timeout=2) as response:
                return response.status == 200
    except Exception:
        return False

def init_tf_dependencies(
    app: FastAPI,
    session_local_factory,
    session_remote_factory,
    rabbitmq_config: dict
):
    reader = TFSerialReader()
    repository = DualTFLunaRepository(session_local_factory, session_remote_factory)
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key"]
    )

    usecase = TFUseCase(reader, repository, publisher, is_connected)
    controller = TFController(usecase)
    app.state.tf_controller = controller