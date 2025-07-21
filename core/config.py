import os
from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class DatabaseEngines:
    local: AIOEngine
    remote: AIOEngine

def get_local_engine() -> AIOEngine:
    uri = os.getenv("MONGODB_URI_LOCAL")
    if not uri:
        raise ValueError("MONGODB_URI_LOCAL no definido en el archivo .env")
    client = AsyncIOMotorClient(uri)
    db_name = uri.split("/")[-1].split("?")[0]
    return AIOEngine(client=client, database=db_name)

def get_remote_engine() -> AIOEngine:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI no definido en el archivo .env")
    client = AsyncIOMotorClient(uri)
    db_name = uri.split("/")[-1].split("?")[0]
    return AIOEngine(client=client, database=db_name)

def get_engine() -> AIOEngine:
    print("⚠️  ADVERTENCIA: get_engine() está deprecado. Usar get_dual_engines().")
    return get_local_engine()

def get_dual_engines() -> DatabaseEngines:
    return DatabaseEngines(
        local=get_local_engine(),
        remote=get_remote_engine()
    )

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
