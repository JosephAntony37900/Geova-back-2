# --- rabbitmq/publisher.py ---
import pika
import json

def publish_data(sensor):
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()
    channel.queue_declare(queue='sensor_data')
    message = json.dumps(sensor.dict())
    channel.basic_publish(exchange='', routing_key='sensor_data', body=message)
    connection.close()