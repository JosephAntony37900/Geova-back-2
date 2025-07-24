import paho.mqtt.client
import json
import time
from MPU6050.domain.ports.mpu_publisher import MPUPublisher
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class RabbitMQMPUPublisher(MPUPublisher):
    def __init__(self, host: str, user: str, password: str, routing_key: str, port: int = 1883):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.routing_key = routing_key
        self.client_id = f"mpu6050_publisher_{int(time.time())}"

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT-MPU] Conectado al broker MQTT (RC: {rc})")
        else:
            print(f"[MQTT-MPU] Error de conexión (RC: {rc})")

    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT-MPU] Mensaje publicado (MID: {mid})")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"[MQTT-MPU] Desconexión inesperada (RC: {rc})")

    def publish(self, sensor: SensorMPU):
        try:
            # Crear cliente MQTT
            client = mqtt.Client(client_id=self.client_id, clean_session=True)
            
            # Configurar callbacks
            client.on_connect = self._on_connect
            client.on_publish = self._on_publish
            client.on_disconnect = self._on_disconnect
            
            # Configurar credenciales si se proporcionan
            if self.user and self.password:
                client.username_pw_set(self.user, self.password)
            
            # Conectar al broker
            client.connect(self.host, self.port, keepalive=60)
            client.loop_start()
            
            # Preparar mensaje
            message = json.dumps(sensor.dict(), default=str)
            
            # Publicar mensaje con QoS 1 (at least once delivery)
            result = client.publish(
                topic=self.routing_key,
                payload=message,
                qos=1,
                retain=False
            )
            
            # Esperar confirmación de publicación
            result.wait_for_publish(timeout=5)
            
            print(f"MPU6050 publicado: {message}")
            conn.close()

        except ConnectionRefusedError:
            print("[MQTT-MPU] No hay conexión a RabbitMQ (¿sin internet?). Solo local.")
        except TimeoutError:
            print("[MQTT-MPU] Timeout al conectar con el broker MQTT")
        except Exception as e:
            print(f"[MQTT-MPU] Error inesperado al publicar: {e}")