# TFLuna/infraestructure/mqtt/publisher.py
from TFLuna.domain.ports.mqtt_publisher import MQTTPublisher
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
import pika, json

class RabbitMQPublisher(MQTTPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: SensorTF):
        credentials = pika.PlainCredentials(self.user, self.password)
        conn = pika.BlockingConnection(pika.ConnectionParameters(self.host, credentials=credentials))
        ch = conn.channel()
        ch.exchange_declare(exchange="amq.topic", exchange_type="topic", durable=True)

        message = json.dumps(sensor.dict(), default=str)
        ch.basic_publish(exchange="amq.topic", routing_key=self.routing_key, body=message)

        print(f"✅ MQTT enviado: {message}")
        conn.close()
