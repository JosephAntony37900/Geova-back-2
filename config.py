# --- config.py ---
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)

# Toma el nombre de la base desde la URI
db_name = MONGODB_URI.split("/")[-1].split("?")[0]
engine = AIOEngine(client=client, database=db_name)
