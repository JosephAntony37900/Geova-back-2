# core/config.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

# SQLite local
def get_local_engine():
    sqlite_uri = os.getenv("SQLITE_DB_URI", "sqlite+aiosqlite:///./local.db")
    engine = create_async_engine(sqlite_uri, echo=False)
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# PostgreSQL remoto
def get_remote_engine():
    pg_uri = os.getenv("POSTGRES_DB_URI")
    if not pg_uri:
        raise ValueError("POSTGRES_DB_URI no definido en el .env")
    engine = create_async_engine(pg_uri, echo=False)
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

def get_rabbitmq_config():
    return {
        "host": os.getenv("RABBITMQ_HOST"),
        "user": os.getenv("RABBITMQ_USER"),
        "pass": os.getenv("RABBITMQ_PASS"),
        "routing_key": os.getenv("ROUTING_KEY_TF"),
        "routing_key_imx": os.getenv("ROUTING_KEY_IMX477"),
        "routing_key_mpu": os.getenv("ROUTING_KEY_MPU6050"),
        "routing_key_hc": os.getenv("ROUTING_KEY_HC"),
    }