# IMX477/infraestructure/streaming/camera_config.py
"""
Configuraciones optimizadas para el streaming de la cámara IMX477
"""

# Configuración de resolución y calidad
STREAM_CONFIGS = {
    "high_quality": {
        "width": 1920,
        "height": 1080,
        "quality": 90,
        "fps": 15
    },
    "medium_quality": {
        "width": 1280,
        "height": 720,
        "quality": 85,
        "fps": 25
    },
    "low_latency": {
        "width": 640,
        "height": 480,
        "quality": 80,
        "fps": 30
    },
    "infrared_optimized": {
        "width": 640,
        "height": 480,
        "quality": 85,
        "fps": 30,
        "infrared": True
    }
}

# Configuración por defecto (optimizada para latencia baja)
DEFAULT_CONFIG = STREAM_CONFIGS["low_latency"]

# Comandos libcamera optimizados
LIBCAMERA_BASE_CMD = [
    "libcamera-still",
    "-n",  # No preview
    "--immediate",  # Captura inmediata
    "--encoding", "jpg",
    "--quality", "85"
]

# Optimizaciones para infrarrojo
INFRARED_ENHANCEMENTS = {
    "brightness": "0.1",
    "contrast": "1.2",
    "gamma": "0.8"
}