# --- src/rabbitmq/publisher.py ---
import pika
import json
from datetime import datetime
from config import RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS
from bson import ObjectId

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def publish_data(sensor, routing_key):
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()

    # Declarar el exchange topic
    channel.exchange_declare(exchange="amq.topic", exchange_type="topic", durable=True)

    # Publicar con routing key
    message = json.dumps(sensor.dict(), default=default_serializer)
    channel.basic_publish(exchange="amq.topic", routing_key=routing_key, body=message)

    print(f"✅ Enviado a RabbitMQ: {routing_key} → {message}")
    connection.close()
