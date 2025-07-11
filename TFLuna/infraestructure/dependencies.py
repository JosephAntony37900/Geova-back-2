# TFLuna/infraestructure/dependencies.py
from fastapi import FastAPI
from odmantic import AIOEngine

from TFLuna.infraestructure.serial.tf_serial_reader import TFSerialReader
from TFLuna.infraestructure.repositories.tf_repo_mongo import TFLunaRepositoryMongo
from TFLuna.infraestructure.mqtt.publisher import RabbitMQPublisher
from TFLuna.application.tf_usecases import TFUseCase
from TFLuna.infraestructure.controllers.controller_tf import TFController

def init_tf_dependencies(app: FastAPI, engine: AIOEngine, rabbitmq_config: dict):
    reader = TFSerialReader()
    repository = TFLunaRepositoryMongo(engine)
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key"]
    )

    usecase = TFUseCase(reader, repository, publisher)
    controller = TFController(usecase)

    app.state.tf_controller = controller
