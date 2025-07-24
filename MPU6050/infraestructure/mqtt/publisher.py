# MPU6050/infraestructure/mqtt/publisher.py
from MPU6050.domain.ports.mpu_publisher import MPUPublisher
from MPU6050.domain.entities.sensor_mpu import SensorMPU
import pika, json
from pika.exceptions import AMQPConnectionError

class RabbitMQMPUPublisher(MPUPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: SensorMPU):
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            conn = pika.BlockingConnection(pika.ConnectionParameters(self.host, credentials=credentials))
            ch = conn.channel()

            # Asegurar exchange y publicar
            ch.exchange_declare(exchange="amq.topic", exchange_type="topic", durable=True)
            message = json.dumps(sensor.dict(), default=str)
            ch.basic_publish(exchange="amq.topic", routing_key=self.routing_key, body=message)

            print(f"[MQTT-MPU] Mensaje enviado: {message}")
            conn.close()

        except AMQPConnectionError:
            print("[MQTT-MPU] No hay conexión a RabbitMQ. Solo local.")
        except Exception as e:
            print(f"[MQTT-MPU] Error inesperado al publicar: {e}")