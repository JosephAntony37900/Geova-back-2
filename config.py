# --- config.py ---
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
ROUTING_KEY_TF = os.getenv("ROUTING_KEY_TF")
ROUTING_KEY_IMX477 = os.getenv("ROUTING_KEY_IMX477")
ROUTING_KEY_GRAPH = os.getenv("ROUTING_KEY_GRAPH")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_USER = os.getenv("RABBITMQ_USER")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS")
client = AsyncIOMotorClient(MONGODB_URI)

# Toma el nombre de la base desde la URI
db_name = MONGODB_URI.split("/")[-1].split("?")[0]
engine = AIOEngine(client=client, database=db_name)
