# MPU6050/infraestructure/dependencies.py
from fastapi import FastAPI
from odmantic import AIOEngine

from MPU6050.infraestructure.serial.mpu_serial_reader import MPUSerialReader
from MPU6050.infraestructure.repositories.mpu_repo_mongo import MPURepositoryMongo
from MPU6050.infraestructure.mqtt.publisher import RabbitMQMPUPublisher
from MPU6050.application.mpu_usecase import MPUUseCase
from MPU6050.infraestructure.controllers.controller_mpu import MPUController

def init_mpu_dependencies(app: FastAPI, engine: AIOEngine, rabbitmq_config: dict):
    reader = MPUSerialReader()
    repository = MPURepositoryMongo(engine)
    publisher = RabbitMQMPUPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key"]
    )

    usecase = MPUUseCase(reader, repository, publisher)
    controller = MPUController(usecase)

    app.state.mpu_controller = controller
