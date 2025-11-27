# HCSR04/infraestructure/mqtt/publisher.py
from HCSR04.domain.ports.mqtt_publisher import MQTTPublisher
from HCSR04.domain.entities.hc_sensor import HCSensorData
from core.rabbitmq_pool import get_rabbitmq_pool


class RabbitMQPublisher(MQTTPublisher):
    """
    Publisher de RabbitMQ que usa el pool de conexiones compartido.
    No bloqueante - encola mensajes para publicación async.
    """
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: HCSensorData):
        """Publica usando el pool compartido (no bloqueante)."""
        try:
            pool = get_rabbitmq_pool(self.host, self.user, self.password)
            pool.publish(
                routing_key=self.routing_key,
                body=sensor.dict()
            )
        except Exception as e:
            print(f"[MQTT-HC] Error al encolar mensaje: {e}")