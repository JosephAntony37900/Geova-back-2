# IMX477/infraestructure/streaming/streamer.py
import subprocess
import psutil
import asyncio
from typing import Optional, Generator
import logging
import threading
import numpy as np
import cv2

logger = logging.getLogger(__name__)

# Instancia global singleton para compartir entre módulos
_streamer_instance: Optional['Streamer'] = None

def get_streamer() -> 'Streamer':
    """Obtiene la instancia global del streamer (singleton)"""
    global _streamer_instance
    if _streamer_instance is None:
        _streamer_instance = Streamer()
    return _streamer_instance

class Streamer:
    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self.is_streaming = False
        # Frame compartido para análisis
        self._current_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._frame_updated = threading.Event()
        # Contador para actualizar frame compartido solo cada N frames
        self._frame_counter = 0
        self._update_every_n_frames = 10
        
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Obtiene una copia del frame actual del streaming para análisis."""
        with self._frame_lock:
            if self._current_frame is not None:
                return self._current_frame.copy()
            return None
    
    def _update_frame(self, jpeg_bytes: bytes):
        """Actualiza el frame actual desde bytes JPEG."""
        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                with self._frame_lock:
                    self._current_frame = frame
                self._frame_updated.set()
        except Exception as e:
            logger.error(f"Error actualizando frame: {e}")
    
    async def wait_for_frame(self, timeout: float = 2.0) -> Optional[np.ndarray]:
        """Espera hasta que haya un nuevo frame disponible."""
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None, 
                lambda: self._frame_updated.wait(timeout=timeout)
            )
            self._frame_updated.clear()
            return self.get_current_frame()
        except Exception as e:
            logger.error(f"Error esperando frame: {e}")
            return None
        
    def kill_zombie_rpicam(self):
        """Matar cualquier proceso zombie de rpicam."""
        try:
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = p.info.get('cmdline')
                if cmdline and ('rpicam-vid' in ' '.join(cmdline) or 'rpicam-still' in ' '.join(cmdline)):
                    try:
                        p.kill()
                        logger.info(f"Proceso rpicam zombie eliminado: PID {p.pid}")
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar proceso zombie: {e}")
        except Exception as e:
            logger.error(f"Error al buscar procesos zombie: {e}")
    
    async def start_stream(self) -> bool:
        """Inicia el streaming de video."""
        try:
            self.kill_zombie_rpicam()
            
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
                self.proc.wait()
                self.proc = None
                await asyncio.sleep(0.5)
            
            logger.info("🎬 Iniciando rpicam-vid...")
            
            # Comando optimizado para BAJA LATENCIA
            self.proc = subprocess.Popen(
                [
                    "rpicam-vid", 
                    "--nopreview", 
                    "-t", "0",
                    "--codec", "mjpeg", 
                    "--quality", "70",
                    "--width", "640", 
                    "--height", "480", 
                    "--framerate", "30",
                    "--flush",  # Flush cada frame - reduce latencia
                    "-o", "-"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Sin buffer - mínima latencia
            )
            
            await asyncio.sleep(1.5)
            
            if self.proc.poll() is not None:
                stderr_output = ""
                if self.proc.stderr:
                    try:
                        stderr_output = self.proc.stderr.read().decode()
                    except:
                        pass
                logger.error(f"rpicam-vid falló al iniciar: {stderr_output}")
                return False
            
            self.is_streaming = True
            logger.info("✅ Streaming iniciado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar streaming: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop_stream(self) -> bool:
        """Detiene el streaming de video."""
        try:
            self.is_streaming = False
            
            if self.proc is not None:
                if self.proc.poll() is None:
                    self.proc.terminate()
                    try:
                        self.proc.wait(timeout=2)
                    except:
                        self.proc.kill()
                self.proc = None
                logger.info("🛑 Streaming detenido correctamente")
            
            self.kill_zombie_rpicam()
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
    
    def generate_frames(self) -> Generator[bytes, None, None]:
        """Generador SÍNCRONO de frames para streaming HTTP - versión simple y confiable."""
        if self.proc is None or self.proc.poll() is not None:
            logger.error("No hay proceso activo para generar frames")
            return
        
        buffer = b""
        frame_count = 0
        
        logger.info("📺 Iniciando generación de frames...")
        
        try:
            while self.proc and self.proc.poll() is None and self.is_streaming:
                # Lectura bloqueante simple - más confiable
                chunk = self.proc.stdout.read(4096)
                
                if not chunk:
                    logger.warning("EOF en stdout de rpicam-vid")
                    break
                
                buffer += chunk
                
                # Buscar frames JPEG completos en el buffer
                while True:
                    # Buscar inicio de JPEG (SOI: 0xFFD8)
                    start = buffer.find(b"\xff\xd8")
                    if start == -1:
                        # No hay inicio, mantener solo últimos bytes por si viene partido
                        if len(buffer) > 2:
                            buffer = buffer[-2:]
                        break
                    
                    # Descartar datos antes del SOI
                    if start > 0:
                        buffer = buffer[start:]
                    
                    # Buscar fin de JPEG (EOI: 0xFFD9)
                    end = buffer.find(b"\xff\xd9", 2)
                    if end == -1:
                        # Frame incompleto, esperar más datos
                        break
                    
                    # Extraer frame completo
                    frame_end = end + 2
                    frame = buffer[:frame_end]
                    buffer = buffer[frame_end:]
                    frame_count += 1
                    
                    # Log cada 30 frames
                    if frame_count % 30 == 0:
                        logger.info(f"📷 Frame #{frame_count} ({len(frame)} bytes)")
                    
                    # Actualizar frame compartido para análisis cada N frames
                    self._frame_counter += 1
                    if self._frame_counter >= self._update_every_n_frames:
                        self._update_frame(frame)
                        self._frame_counter = 0
                    
                    # Yield frame en formato multipart
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" +
                        frame +
                        b"\r\n"
                    )
                
                # Evitar buffer overflow
                if len(buffer) > 200000:
                    logger.warning(f"Buffer muy grande ({len(buffer)}), limpiando...")
                    buffer = buffer[-50000:]
                    
        except GeneratorExit:
            logger.info("Cliente desconectado")
        except Exception as e:
            logger.error(f"Error generando frames: {e}")
            import traceback
            traceback.print_exc()
        finally:
            logger.info(f"Generación terminada. Total: {frame_count} frames")
    
    def __del__(self):
        """Cleanup al destruir la instancia."""
        if hasattr(self, 'proc') and self.proc:
            try:
                self.proc.kill()
            except:
                pass
