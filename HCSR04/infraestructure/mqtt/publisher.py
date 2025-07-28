# HCSR04/infraestructure/mqtt/publisher.py
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher
from HCSR04.domain.entities.hc_sensor import HCSensorData
import pika
import json
from pika.exceptions import AMQPConnectionError

class RabbitMQPublisher(MQTTPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: HCSensorData):
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            conn = pika.BlockingConnection(pika.ConnectionParameters(self.host, credentials=credentials))
            ch = conn.channel()

            ch.exchange_declare(exchange="amq.topic", exchange_type="topic", durable=True)
            message = json.dumps(sensor.dict(), default=str)
            ch.basic_publish(exchange="amq.topic", routing_key=self.routing_key, body=message)

            print(f"[MQTT-HC] Mensaje enviado: {message}")
            conn.close()

        except AMQPConnectionError:
            print("[MQTT-HC] No hay conexión a RabbitMQ. Solo local.")
        except Exception as e:
            print(f"[MQTT-HC] Error inesperado al publicar: {e}")