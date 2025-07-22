import pika, json
from pika.exceptions import AMQPConnectionError
from MPU6050.domain.ports.mpu_publisher import MPUPublisher
from MPU6050.domain.entities.sensor_mpu import SensorMPU

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

            # Declarar exchange
            ch.exchange_declare(exchange="mpu.topic", exchange_type="topic", durable=True)

            # Asegurar cola y binding
            ch.queue_declare(queue=self.routing_key, durable=True)
            ch.queue_bind(exchange="mpu.topic", queue=self.routing_key, routing_key=self.routing_key)

            # Publicar mensaje
            message = json.dumps(sensor.dict(), default=str)
            ch.basic_publish(exchange="mpu.topic", routing_key=self.routing_key, body=message)

            print(f"MPU6050 publicado: {message}")
            conn.close()

        except AMQPConnectionError:
            print("[MQTT-MPU] No hay conexión a RabbitMQ (¿sin internet?). Solo local.")
        except Exception as e:
            print(f"[MQTT-MPU] Error inesperado al publicar: {e}")
