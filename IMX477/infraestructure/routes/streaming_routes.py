# IMX477/infraestructure/routes/streaming_routes.py
from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from IMX477.infraestructure.streaming.streamer import get_streamer
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/imx477/streaming")


@router.get("/ping")
@router.head("/ping")
def streaming_ping():
    """
    Ping SÍNCRONO ultra-ligero para verificar que el servicio de streaming existe.
    NO verifica estado del streaming, solo que la API responde.
    """
    return {"pong": True}


@router.post("/start")
async def start_streaming():
    """Inicia el streaming de video."""
    try:
        streamer = get_streamer()
        logger.info("📷 Iniciando streaming de video...")
        success = await streamer.start_stream()
        
        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Stream iniciado correctamente",
                    "active": True
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="No se pudo iniciar el streaming. Verifique que la cámara esté disponible."
            )
            
    except Exception as e:
        logger.error(f"Error al iniciar streaming: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al iniciar streaming: {str(e)}"
        )

@router.post("/stop")
async def stop_streaming():
    """Detiene el streaming de video."""
    try:
        streamer = get_streamer()
        logger.info("🛑 Deteniendo streaming de video...")
        success = await streamer.stop_stream()
        
        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Stream detenido correctamente",
                    "active": False
                }
            )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "No había streaming activo",
                    "active": False
                }
            )
            
    except Exception as e:
        logger.error(f"Error al detener streaming: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al detener streaming: {str(e)}"
        )

@router.get("/status")
@router.head("/status")
def get_streaming_status():
    """
    Obtiene el estado actual del streaming - SÍNCRONO para respuesta inmediata.
    get_status() es una operación síncrona que no bloquea.
    """
    try:
        streamer = get_streamer()
        status = streamer.get_status()
        return JSONResponse(
            status_code=200,
            content=status
        )
    except Exception as e:
        logger.error(f"Error al obtener estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al obtener estado: {str(e)}"
        )

@router.get("/video")
def video_feed():
    """Stream de video en tiempo real - versión SÍNCRONA como tu API de prueba."""
    try:
        streamer = get_streamer()
        # Verificar que el streaming esté activo
        status = streamer.get_status()
        if not status["active"]:
            return Response(
                status_code=503,
                content="Stream no está activo. Inicie el streaming primero con /start"
            )
        
        logger.info("📺 Iniciando feed de video...")
        
        return StreamingResponse(
            streamer.generate_frames(),
            media_type="multipart/x-mixed-replace; boundary=frame",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Connection": "close"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en video feed: {e}")
        return Response(
            status_code=500,
            content=f"Error interno en video feed: {str(e)}"
        )

@router.get("/health")
@router.head("/health")
def streaming_health():
    """Health check SÍNCRONO específico para streaming."""
    try:
        streamer = get_streamer()
        status = streamer.get_status()
        return JSONResponse(
            status_code=200,
            content={
                "service": "IMX477 Streaming",
                "status": "healthy",
                "streaming_active": status["active"],
                "fps": status["fps"],
                "camera_available": True
            }
        )
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "service": "IMX477 Streaming",
                "status": "unhealthy",
                "error": str(e)
            }
        )