import os
import tempfile
import subprocess
import logging
import shutil
from typing import Tuple
import aiofiles
from fastapi import UploadFile
from .audio_service import AudioService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoService:
    """Service for processing uploaded video files and extracting audio for transcription."""
    
    def __init__(self):
        self.audio_service = AudioService()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        # Use the same FFmpeg setup as AudioService
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_dir = os.path.join(backend_root, 'tools', 'ffmpeg')
        self.ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg')
        
        # Check if local FFmpeg binaries exist and are executable
        if os.path.exists(self.ffmpeg_path) and os.access(self.ffmpeg_path, os.X_OK):
            logger.info(f"✅ FFmpeg local encontrado para extração de áudio: {self.ffmpeg_path}")
        else:
            logger.warning(f"⚠️ FFmpeg local não encontrado: {self.ffmpeg_path}")
            self.ffmpeg_path = None
    
    async def save_uploaded_video(self, file: UploadFile) -> Tuple[str, float]:
        """Save uploaded video file and return filepath and duration."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Get file extension
        if file.filename:
            _, ext = os.path.splitext(file.filename)
        else:
            ext = '.mp4'  # default extension
        
        # Save uploaded file
        temp_file_path = os.path.join(temp_dir, f"uploaded_video{ext}")
        
        try:
            async with aiofiles.open(temp_file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"📁 Vídeo salvo: {temp_file_path}")
            
            # Get video duration
            duration = await self._get_video_duration(temp_file_path)
            
            return temp_file_path, duration
            
        except Exception as e:
            # Clean up on error
            self._cleanup_temp_dir(temp_dir)
            raise Exception(f"Erro ao processar arquivo de vídeo: {str(e)}")
    
    async def _get_video_duration(self, video_file: str) -> float:
        """Get video file duration using FFprobe."""
        if not self.ffmpeg_path:
            return 0.0
        
        try:
            # Use ffprobe to get duration
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            if not os.path.exists(ffprobe_path):
                ffprobe_path = self.ffmpeg_path  # fallback to ffmpeg
            
            cmd = [
                ffprobe_path, "-v", "quiet", "-show_entries", 
                "format=duration", "-of", "csv=p=0", video_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter duração do vídeo: {e}")
        
        return 0.0
    
    async def extract_audio_from_video(self, video_file: str) -> str:
        """Extract audio from video file and convert to WAV format."""
        if not self.ffmpeg_path:
            raise Exception("FFmpeg não disponível para extração de áudio")
        
        # Create audio file path
        audio_file = os.path.splitext(video_file)[0] + '_extracted.wav'
        
        try:
            # Extract audio from video and convert to WAV
            cmd = [
                self.ffmpeg_path, "-i", video_file, 
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",  # Mono
                audio_file, "-y"  # Overwrite output
            ]
            
            logger.info(f"🎵 Extraindo áudio do vídeo: {video_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Áudio extraído com sucesso: {audio_file}")
                return audio_file
            else:
                logger.error(f"❌ Erro na extração de áudio: {result.stderr}")
                raise Exception(f"Erro na extração de áudio: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Erro na extração de áudio: {e}")
            raise Exception(f"Erro na extração de áudio: {str(e)}")
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def cleanup_temp_file(self, filepath: str):
        """Clean up temporary video file."""
        try:
            if os.path.exists(filepath):
                temp_dir = os.path.dirname(filepath)
                self._cleanup_temp_dir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def process_video_file(self, file: UploadFile, language: str = "auto", output_format: str = "txt") -> dict:
        """Complete pipeline: save video, extract audio, and transcribe."""
        video_file = None
        audio_file = None
        
        try:
            # Save uploaded video file
            video_file, duration = await self.save_uploaded_video(file)
            
            # Extract audio from video
            audio_file = await self.extract_audio_from_video(video_file)
            
            # Use AudioService to transcribe the extracted audio
            if output_format == "srt":
                transcription, detected_language, segments = await self.audio_service.transcribe_audio_with_timestamps(audio_file, language)
                formatted_output = self.audio_service._format_srt_timestamps(segments)
            else:
                transcription, detected_language = await self.audio_service.transcribe_audio(audio_file, language)
                formatted_output = transcription
            
            return {
                "transcription": formatted_output,
                "duration": duration,
                "language": detected_language,
                "output_format": output_format,
                "filename": file.filename,
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
        finally:
            # Clean up temporary files
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except Exception:
                    pass
            if video_file:
                await self.cleanup_temp_file(video_file)