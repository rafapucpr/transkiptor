import os
import tempfile
import subprocess
import logging
from typing import Tuple, Optional
import yt_dlp
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoDownloadService:
    def __init__(self):
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required dependencies are available."""
        # Use local FFmpeg binaries from backend/tools/ffmpeg
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_dir = os.path.join(backend_root, 'tools', 'ffmpeg')
        self.ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg')
        self.ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe')
        
        # Check if local FFmpeg binaries exist and are executable
        if os.path.exists(self.ffmpeg_path) and os.access(self.ffmpeg_path, os.X_OK):
            logger.info(f"✅ FFmpeg local encontrado: {self.ffmpeg_path}")
            if os.path.exists(self.ffprobe_path) and os.access(self.ffprobe_path, os.X_OK):
                logger.info(f"✅ FFprobe local encontrado: {self.ffprobe_path}")
            else:
                logger.warning(f"⚠️ FFprobe não encontrado: {self.ffprobe_path}")
        else:
            logger.error(f"❌ FFmpeg local não encontrado: {self.ffmpeg_path}")
            self.ffmpeg_path = None
            self.ffprobe_path = None
    
    async def download_video(self, url: str) -> Tuple[str, str, dict]:
        """Download video from YouTube URL and return filepath, filename and metadata."""
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        
        # Configure for best quality video + audio (prioritize 1080p but allow higher)
        ydl_opts = {
            'format': 'bestvideo[height>=1080]+bestaudio/bestvideo+bestaudio/best',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'quiet': False,  # Allow some output for debugging
            'no_warnings': False,
            'extract_flat': False,
        }
        
        # Configure FFmpeg for yt-dlp
        if self.ffmpeg_path:
            ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
            
            # Set FFmpeg location for yt-dlp
            ydl_opts['ffmpeg_location'] = ffmpeg_dir
            
            # Add FFmpeg directory to PATH
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path:
                os.environ['PATH'] = f"{ffmpeg_dir}:{current_path}"
                logger.info(f"🔧 FFmpeg adicionado ao PATH: {ffmpeg_dir}")
            
            # Set environment variables
            os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
            if self.ffprobe_path:
                os.environ['FFPROBE_BINARY'] = self.ffprobe_path
            else:
                os.environ['FFPROBE_BINARY'] = self.ffmpeg_path
        
        try:
            logger.info(f"📥 Iniciando download do vídeo: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', 0)
                title = info.get('title', 'unknown')
                uploader = info.get('uploader', 'unknown')
                view_count = info.get('view_count', 0)
                width = info.get('width', 'unknown')
                height = info.get('height', 'unknown')
                format_id = info.get('format_id', 'unknown')
                
                logger.info(f"📁 Título: {title}")
                logger.info(f"⏱️ Duração: {duration}s")
                logger.info(f"📺 Resolução: {width}x{height}")
                logger.info(f"🎬 Format ID: {format_id}")
                
                # Find the downloaded video file
                video_file = None
                files_in_dir = os.listdir(temp_dir)
                logger.info(f"📂 Arquivos baixados: {files_in_dir}")
                
                # Look for MP4 first, then other formats
                for file in files_in_dir:
                    if file.endswith('.mp4'):
                        video_file = os.path.join(temp_dir, file)
                        logger.info(f"🎬 Arquivo MP4 encontrado: {video_file}")
                        break
                
                if not video_file:
                    # Fallback to other video formats
                    video_extensions = ['.mkv', '.webm', '.avi', '.mov', '.flv']
                    for file in files_in_dir:
                        for ext in video_extensions:
                            if file.endswith(ext):
                                video_file = os.path.join(temp_dir, file)
                                logger.info(f"🎬 Arquivo de vídeo encontrado: {video_file}")
                                break
                        if video_file:
                            break
                
                if not video_file:
                    raise Exception("Arquivo de vídeo não encontrado após download")
                
                # Generate safe filename
                safe_title = self._sanitize_filename(title)
                filename = f"{safe_title}.mp4"
                
                metadata = {
                    'title': title,
                    'duration': duration,
                    'uploader': uploader,
                    'view_count': view_count,
                    'original_url': url
                }
                
                return video_file, filename, metadata
                
        except yt_dlp.DownloadError as e:
            # Clean up temp directory on error
            self._cleanup_temp_dir(temp_dir)
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                raise Exception("Vídeo não está disponível para download (pode estar restrito geograficamente ou privado)")
            elif "404" in error_msg or "Not Found" in error_msg:
                raise Exception("Vídeo não encontrado. Verifique se a URL está correta")
            elif "age" in error_msg.lower() or "sign" in error_msg.lower():
                raise Exception("Vídeo requer verificação de idade ou login. Tente outro vídeo")
            else:
                raise Exception(f"Erro ao baixar vídeo: {error_msg}")
        except Exception as e:
            # Clean up temp directory on error
            self._cleanup_temp_dir(temp_dir)
            if "HTTP Error" in str(e):
                raise Exception("Erro de conexão com YouTube. Tente novamente em alguns minutos")
            raise Exception(f"Erro inesperado no download: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage."""
        # Replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\s]+', ' ', filename)  # Multiple spaces to single
        filename = filename.strip()
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200].strip()
        
        return filename or "video"
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def cleanup_temp_file(self, filepath: str):
        """Clean up temporary video file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                # Also remove the directory if it's empty
                temp_dir = os.path.dirname(filepath)
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors