# MPU6050/infraestructure/mqtt/publisher.py
import pika, json
from MPU6050.domain.ports.mpu_publisher import MPUPublisher
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class RabbitMQMPUPublisher(MPUPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str):
        self.host = host
        self.user = user
        self.password = password
        self.routing_key = routing_key

    def publish(self, sensor: SensorMPU):
        credentials = pika.PlainCredentials(self.user, self.password)
        conn = pika.BlockingConnection(pika.ConnectionParameters(self.host, credentials=credentials))
        ch = conn.channel()
        ch.exchange_declare(exchange="mpu.topic", exchange_type="topic", durable=True)

        message = json.dumps(sensor.dict(), default=str)
        ch.basic_publish(exchange="mpu.topic", routing_key=self.routing_key, body=message)

        print(f"MPU6050 publicado: {message}")
        conn.close()
