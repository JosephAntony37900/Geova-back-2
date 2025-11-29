# core/rabbitmq_pool.py
"""
Pool de conexiones RabbitMQ con publicación no bloqueante.
Patrón: Connection Pool + Producer/Consumer con Queue interna
"""
import asyncio
import json
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any, Dict
from dataclasses import dataclass
from queue import Queue, Empty
from threading import Thread, Event
import time


@dataclass
class PublishMessage:
    """Mensaje para publicar en la cola."""
    routing_key: str
    body: dict
    exchange: str = "amq.topic"


class RabbitMQPool:
    """
    Pool de conexiones RabbitMQ con publicación asíncrona.
    
    Características:
    - Conexión persistente (no abre/cierra por cada mensaje)
    - Cola interna para publicación no bloqueante
    - Reconexión automática
    - Thread dedicado para publicación
    """
    _instance: Optional['RabbitMQPool'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        host: str = "localhost",
        user: str = "guest",
        password: str = "guest",
        port: int = 5672
    ):
        if self._initialized:
            return
        self._initialized = True
        
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None
        self._message_queue: Queue[PublishMessage] = Queue(maxsize=1000)
        self._stop_event = Event()
        self._publisher_thread: Optional[Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="rabbitmq")
        self._is_connected = False
        self._reconnect_delay = 5  # segundos entre intentos de reconexión
        self._last_reconnect_attempt = 0
    
    def _connect(self) -> bool:
        """Establece conexión con RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(self.user, self.password)
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=credentials,
                    heartbeat=60,
                    blocked_connection_timeout=30
                )
            )
            self._channel = self._connection.channel()
            self._channel.exchange_declare(
                exchange="amq.topic",
                exchange_type="topic",
                durable=True
            )
            self._is_connected = True
            print("[RabbitMQ] Conexión establecida")
            return True
        except Exception as e:
            print(f"[RabbitMQ] Error al conectar: {e}")
            self._is_connected = False
            return False
    
    def _reconnect(self) -> bool:
        """Intenta reconectar respetando el delay."""
        current_time = time.time()
        if current_time - self._last_reconnect_attempt < self._reconnect_delay:
            return False
        
        self._last_reconnect_attempt = current_time
        self._close_connection()
        return self._connect()
    
    def _close_connection(self):
        """Cierra la conexión de forma segura."""
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
        except Exception:
            pass
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception:
            pass
        self._channel = None
        self._connection = None
        self._is_connected = False
    
    def _publisher_loop(self):
        """Loop del thread de publicación."""
        print("[RabbitMQ] Thread de publicación iniciado")
        
        while not self._stop_event.is_set():
            try:
                # Obtener mensaje de la cola (timeout para poder verificar stop_event)
                try:
                    msg = self._message_queue.get(timeout=0.5)
                except Empty:
                    continue
                
                # Verificar/establecer conexión
                if not self._is_connected:
                    if not self._reconnect():
                        # No pudimos conectar, descartar mensaje o re-encolar
                        # Por ahora lo descartamos con log
                        print(f"[RabbitMQ] Mensaje descartado (sin conexión): {msg.routing_key}")
                        continue
                
                # Publicar mensaje
                try:
                    body = json.dumps(msg.body, default=str)
                    self._channel.basic_publish(
                        exchange=msg.exchange,
                        routing_key=msg.routing_key,
                        body=body,
                        properties=pika.BasicProperties(
                            delivery_mode=1  # No persistente (más rápido para sensores)
                        )
                    )
                except (AMQPConnectionError, AMQPChannelError) as e:
                    print(f"[RabbitMQ] Error de conexión al publicar: {e}")
                    self._is_connected = False
                except Exception as e:
                    print(f"[RabbitMQ] Error al publicar: {e}")
                    
            except Exception as e:
                print(f"[RabbitMQ] Error en publisher loop: {e}")
        
        self._close_connection()
        print("[RabbitMQ] Thread de publicación finalizado")
    
    def start(self):
        """Inicia el thread de publicación."""
        if self._publisher_thread is None or not self._publisher_thread.is_alive():
            self._stop_event.clear()
            self._publisher_thread = Thread(
                target=self._publisher_loop,
                name="rabbitmq-publisher",
                daemon=True
            )
            self._publisher_thread.start()
    
    def stop(self):
        """Detiene el thread de publicación."""
        self._stop_event.set()
        if self._publisher_thread and self._publisher_thread.is_alive():
            self._publisher_thread.join(timeout=5)
    
    def publish(self, routing_key: str, body: dict, exchange: str = "amq.topic"):
        """
        Encola un mensaje para publicación (no bloqueante).
        """
        try:
            msg = PublishMessage(routing_key=routing_key, body=body, exchange=exchange)
            self._message_queue.put_nowait(msg)
        except Exception as e:
            print(f"[RabbitMQ] Cola llena, mensaje descartado: {e}")
    
    async def publish_async(self, routing_key: str, body: dict, exchange: str = "amq.topic"):
        """
        Versión async de publish (usa run_in_executor para no bloquear).
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            lambda: self.publish(routing_key, body, exchange)
        )
    
    @property
    def is_connected(self) -> bool:
        """Estado de conexión actual."""
        return self._is_connected
    
    @property
    def queue_size(self) -> int:
        """Tamaño actual de la cola de mensajes."""
        return self._message_queue.qsize()


# Singleton global
_pool: Optional[RabbitMQPool] = None

def get_rabbitmq_pool(
    host: str = "localhost",
    user: str = "guest", 
    password: str = "guest",
    port: int = 5672
) -> RabbitMQPool:
    """Obtiene o crea el pool de conexiones RabbitMQ."""
    global _pool
    if _pool is None:
        _pool = RabbitMQPool(host, user, password, port)
    return _pool

def init_rabbitmq_pool(host: str, user: str, password: str, port: int = 5672):
    """Inicializa y arranca el pool de RabbitMQ."""
    pool = get_rabbitmq_pool(host, user, password, port)
    pool.start()
    return pool

def stop_rabbitmq_pool():
    """Detiene el pool de RabbitMQ."""
    global _pool
    if _pool:
        _pool.stop()
