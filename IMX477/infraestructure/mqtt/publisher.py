from IMX477.domain.ports.mqtt_publisher import MQTTPublisher
from IMX477.domain.entities.sensor_imx import SensorIMX477
import pika, json

class RabbitMQPublisher(MQTTPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: SensorIMX477):
        credentials = pika.PlainCredentials(self.user, self.password)
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(self.host, credentials=credentials)
        )
        ch = conn.channel()
        ch.exchange_declare(exchange="amq.topic", exchange_type="topic", durable=True)
        message = json.dumps(sensor.dict(), default=str)
        ch.basic_publish(exchange="amq.topic", routing_key=self.routing_key, body=message)
        print(f"📤 Enviado IMX477 a RabbitMQ: {message}")
        conn.close()
