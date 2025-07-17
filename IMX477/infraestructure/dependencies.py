from IMX477.application.sensor_imx import IMXUseCase
from IMX477.infraestructure.controllers.controller_imx import IMXController
from IMX477.infraestructure.camera.imx_reader import IMXReader
from IMX477.infraestructure.repositories.imx_repo_mongo import IMXRepositoryMongo
from IMX477.infraestructure.mqtt.publisher import RabbitMQPublisher

def init_imx_dependencies(app, engine, rabbitmq_config):
    reader = IMXReader()
    repository = IMXRepositoryMongo(engine)
    
    publisher = RabbitMQPublisher(
        host=rabbitmq_config["host"],
        user=rabbitmq_config["user"],
        password=rabbitmq_config["pass"],
        routing_key=rabbitmq_config["routing_key_imx"]
    )

    usecase = IMXUseCase(reader, repository, publisher)
    controller = IMXController(usecase)

    app.state.imx_controller = controller
