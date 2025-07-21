# MPU6050/infraestructure/dependencies.py
from fastapi import FastAPI
from MPU6050.infraestructure.serial.mpu_serial_reader import MPUSerialReader
from MPU6050.infraestructure.mqtt.publisher import RabbitMQMPUPublisher
from MPU6050.application.mpu_usecase import MPUUseCase
from MPU6050.infraestructure.controllers.controller_mpu import MPUController
from MPU6050.infraestructure.repositories.mpu_repo_dual import DualMPURepository

def init_mpu_dependencies(
    app: FastAPI,
    session_local_factory,
    session_remote_factory,
    rabbitmq_config: dict,
    is_connected_fn
):
    reader = MPUSerialReader()
    repository = DualMPURepository(session_local_factory, session_remote_factory)
    publisher = RabbitMQMPUPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key_mpu"]
    )

    usecase = MPUUseCase(reader, repository, publisher, is_connected_fn)
    controller = MPUController(usecase)
    app.state.mpu_controller = controller