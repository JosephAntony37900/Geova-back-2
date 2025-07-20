# TFLuna/infraestructure/dependencies.py
from fastapi import FastAPI
from odmantic import AIOEngine
from TFLuna.infraestructure.serial.tf_serial_reader import TFSerialReader
from TFLuna.infraestructure.mqtt.publisher import RabbitMQPublisher
from TFLuna.application.tf_usecases import TFUseCase
from TFLuna.infraestructure.controllers.controller_tf import TFController
from TFLuna.infraestructure.repositories.tf_repo_dual import TFLunaDualRepository

def init_tf_dependencies(
    app: FastAPI,
    local_engine: AIOEngine,
    remote_engine: AIOEngine,
    rabbitmq_config: dict,
    is_connected_fn
):
    reader = TFSerialReader()
    repository = TFLunaDualRepository(local_engine, remote_engine)
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key"]
    )

    usecase = TFUseCase(reader, repository, publisher, is_connected_fn)
    controller = TFController(usecase)
    app.state.tf_controller = controller
