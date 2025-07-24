# IMX477/infraestructure/streaming/streamer.py
import subprocess
import psutil
import asyncio
from typing import Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class Streamer:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.is_streaming = False
        
    def kill_zombie_rpicam(self):
        """Matar cualquier proceso zombie de rpicam-vid."""
        try:
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = p.info.get('cmdline')
                if cmdline and 'rpicam-vid' in ' '.join(cmdline):
                    try:
                        p.kill()
                        logger.info(f"Proceso rpicam-vid zombie eliminado: PID {p.pid}")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar proceso zombie: {e}")
        except Exception as e:
            logger.error(f"Error al buscar procesos zombie: {e}")
    
    async def start_stream(self) -> bool:
        """Inicia el streaming de video."""
        try:
            # Limpieza previa
            self.kill_zombie_rpicam()
            
            # Si ya hay un proceso activo, terminarlo
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
                self.proc = None
                await asyncio.sleep(0.5)  # Dar tiempo para que termine
            
            # Iniciar nuevo proceso
            self.proc = subprocess.Popen(
                [
                    "rpicam-vid", 
                    "--nopreview", 
                    "-t", "0",  # Sin timeout (streaming continuo)
                    "--codec", "mjpeg", 
                    "--quality", "90",
                    "--width", "640", 
                    "--height", "480", 
                    "--framerate", "30", 
                    "-o", "-"  # Output a stdout
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Verificar que el proceso se inició correctamente
            await asyncio.sleep(1)
            if self.proc.poll() is not None:
                # El proceso terminó inesperadamente
                stderr_output = self.proc.stderr.read().decode() if self.proc.stderr else "Sin error específico"
                logger.error(f"rpicam-vid falló al iniciar: {stderr_output}")
                return False
            
            self.is_streaming = True
            logger.info("✅ Streaming iniciado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar streaming: {e}")
            return False
    
    async def stop_stream(self) -> bool:
        """Detiene el streaming de video."""
        try:
            self.kill_zombie_rpicam()
            
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
                self.proc = None
                logger.info("🛑 Streaming detenido correctamente")
            
            self.is_streaming = False
            return True
            
        except Exception as e:
            logger.error(f"Error al detener streaming: {e}")
            return False
    
    def get_status(self) -> dict:
        """Obtiene el estado actual del streaming."""
        if self.proc is None:
            return {"active": False, "fps": 0}
        
        is_active = self.proc.poll() is None and self.is_streaming
        
        return {
            "active": is_active,
            "fps": 30 if is_active else 0
        }
    
    def generate_frames(self) -> AsyncGenerator[bytes, None]:
        """Generador SÍNCRONO de frames para streaming - compatible con tu API de prueba."""
        if self.proc is None or self.proc.poll() is not None:
            logger.error("No hay proceso activo para generar frames")
            return
        
        buffer = b""
        
        try:
            while self.proc and self.proc.poll() is None:
                # Leer chunk de datos (igual que tu API de prueba)
                chunk = self.proc.stdout.read(8192)
                if not chunk:
                    break
                
                buffer += chunk
                
                # Buscar inicio y fin de frame JPEG
                start = buffer.find(b"\xff\xd8")  # SOI (Start of Image)
                end = buffer.find(b"\xff\xd9")    # EOI (End of Image)
                
                if start != -1 and end != -1 and end > start:
                    # Extraer frame completo
                    frame = buffer[start:end+2]
                    buffer = buffer[end+2:]
                    
                    # Yield frame en formato multipart (igual que tu API de prueba)
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        frame +
                        b"\r\n"
                    )
                
                # Evitar que el buffer crezca demasiado
                if len(buffer) > 100000:  # 100KB max
                    buffer = buffer[-50000:]  # Mantener solo los últimos 50KB
                
        except Exception as e:
            logger.error(f"Error generando frames: {e}")
        finally:
            logger.info("Generación de frames terminada")
    
    def __del__(self):
        """Cleanup al destruir la instancia."""
        if hasattr(self, 'proc') and self.proc:
            try:
                self.proc.kill()
            except:
                pass