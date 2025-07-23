# IMX477/infraestructure/routes/streaming_routes.py
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse, JSONResponse
from IMX477.infraestructure.streaming.mjpeg_streamer import mjpeg_streamer
import asyncio

router = APIRouter()

def generate_mjpeg_stream():
    """Generador para el stream MJPEG"""
    while mjpeg_streamer.is_active():
        frame_bytes = mjpeg_streamer.get_current_frame()
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Si no hay frame, enviar frame vacío para mantener conexión
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
        
        # Pequeña pausa para controlar el stream
        import time
        time.sleep(0.033)  # ~30 FPS

@router.post("/imx477/streaming/start")
async def start_streaming():
    """Inicia el streaming de la cámara"""
    try:
        mjpeg_streamer.start_streaming()
        return JSONResponse(content={
            "status": "success",
            "message": "Streaming iniciado correctamente"
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "error", 
            "message": f"Error al iniciar streaming: {str(e)}"
        }, status_code=500)

@router.post("/imx477/streaming/stop")
async def stop_streaming():
    """Detiene el streaming de la cámara"""
    try:
        mjpeg_streamer.stop_streaming()
        return JSONResponse(content={
            "status": "success",
            "message": "Streaming detenido correctamente"
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"Error al detener streaming: {str(e)}"
        }, status_code=500)

@router.get("/imx477/streaming/status")
async def get_streaming_status():
    """Obtiene el estado del streaming"""
    return JSONResponse(content={
        "active": mjpeg_streamer.is_active(),
        "fps": 30
    })

@router.get("/imx477/streaming/video")
async def video_feed():
    """Endpoint para el stream MJPEG"""
    if not mjpeg_streamer.is_active():
        return JSONResponse(content={
            "error": "Streaming no está activo. Inicie el streaming primero."
        }, status_code=400)
    
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )