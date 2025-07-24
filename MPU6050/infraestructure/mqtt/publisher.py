import paho.mqtt.client as mqtt
import json
import time
from MPU6050.domain.ports.mpu_publisher import MPUPublisher
from MPU6050.domain.entities.sensor_mpu import SensorMPU

class RabbitMQMPUPublisher(MPUPublisher):
    def __init__(self, host: str, port: int = 1883, user: str = None, password: str = None, topic: str = "sensors/mpu6050"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.topic = topic
        self.client_id = f"mpu6050_publisher_{int(time.time())}"
        self.client = None
        self.connected = False
        self._setup_client()

    def _setup_client(self):
        """Configurar cliente MQTT"""
        self.client = mqtt.Client(client_id=self.client_id, clean_session=True)
        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish
        self.client.on_disconnect = self._on_disconnect
        
        if self.user and self.password:
            self.client.username_pw_set(self.user, self.password)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"[MQTT-MPU] Conectado al broker MQTT (RC: {rc})")
        else:
            self.connected = False
            print(f"[MQTT-MPU] Error de conexión (RC: {rc})")

    def _on_publish(self, client, userdata, mid):
        print(f"[MQTT-MPU] Mensaje publicado (MID: {mid})")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            print(f"[MQTT-MPU] Desconexión inesperada (RC: {rc})")

    def _ensure_connection(self):
        """Asegurar que hay conexión al broker"""
        if not self.connected:
            try:
                self.client.connect(self.host, self.port, keepalive=60)
                self.client.loop_start()
                # Esperar un poco para la conexión
                time.sleep(0.5)
            except Exception as e:
                print(f"[MQTT-MPU] Error al conectar: {e}")
                return False
        return self.connected

    def publish(self, sensor: SensorMPU):
        try:
            if not self._ensure_connection():
                print("[MQTT-MPU] No hay conexión al broker MQTT. Solo local.")
                return
            
            # Preparar mensaje
            message = json.dumps(sensor.dict(), default=str)
            
            # Publicar mensaje
            result = self.client.publish(
                topic=self.topic,
                payload=message,
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT-MPU] Datos publicados: {message}")
            else:
                print(f"[MQTT-MPU] Error al publicar (RC: {result.rc})")
                
        except Exception as e:
            print(f"[MQTT-MPU] Error inesperado al publicar: {e}")

    def disconnect(self):
        """Desconectar del broker"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            print("[MQTT-MPU] Desconectado del broker MQTT")