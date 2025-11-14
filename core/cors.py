# core/cors.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    """Configurar CORS para permitir requests desde el frontend"""
    
    # Lista de orígenes permitidos
    origins = [
        "http://localhost:3000",    # React development server
        "http://localhost:5173",    # Vite development server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8080",    # Otros posibles puertos
        "http://127.0.0.1:8080",
        "http://raspberrypi.local:3000",  # React en Raspberry Pi
        "http://raspberrypi.local:5173",  # Vite en Raspberry Pi
        "http://raspberrypi.local",  # Raspberry Pi general
        "https://www.geova.pro/",  # Producción
        
        # Agregar más orígenes según sea necesario
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,          # Orígenes permitidos
        allow_credentials=True,         # Permitir cookies/credenciales
        allow_methods=["*"],           # Permitir todos los métodos HTTP (GET, POST, PUT, DELETE, OPTIONS)
        allow_headers=["*"],           # Permitir todos los headers
    )
    
    print("🌐 CORS configurado correctamente")
    print(f"📡 Orígenes permitidos: {origins}")