# --- config.py ---
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "sensores"

client = AsyncIOMotorClient(MONGO_URI)
engine = AIOEngine(motor_client=client, database=DATABASE_NAME)
