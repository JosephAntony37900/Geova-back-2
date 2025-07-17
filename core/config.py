# core/config.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(uri)
    db_name = uri.split("/")[-1].split("?")[0]
    return AIOEngine(client=client, database=db_name)

def get_rabbitmq_config():
    return {
        "host": os.getenv("RABBITMQ_HOST"),
        "user": os.getenv("RABBITMQ_USER"),
        "pass": os.getenv("RABBITMQ_PASS"),
        "routing_key": os.getenv("ROUTING_KEY_TF"),
        "routing_key_imx": os.getenv("ROUTING_KEY_IMX477"),
        "routing_key_mpu": os.getenv("ROUTING_KEY_MPU6050"),
    }
