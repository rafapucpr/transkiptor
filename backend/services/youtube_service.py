import os
import tempfile
import subprocess
import json
import logging
from typing import Tuple, Optional
import yt_dlp
import aiofiles
from .whisper_python_service import WhisperPythonService

# Import imageio_ffmpeg only as fallback
try:
    import imageio_ffmpeg as ffmpeg
    IMAGEIO_FFMPEG_AVAILABLE = True
except ImportError:
    IMAGEIO_FFMPEG_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeService:
    def __init__(self, whisper_path: str = "whisper"):
        self.whisper_path = whisper_path
        self.whisper_python = WhisperPythonService()
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
            logger.warning(f"⚠️ FFmpeg local não encontrado: {self.ffmpeg_path}")
            # Fallback to imageio-ffmpeg if available
            if IMAGEIO_FFMPEG_AVAILABLE:
                try:
                    self.ffmpeg_path = ffmpeg.get_ffmpeg_exe()
                    self.ffprobe_path = None
                    logger.info(f"🔄 Usando imageio-ffmpeg como fallback: {self.ffmpeg_path}")
                except Exception as e:
                    logger.error(f"❌ Erro ao usar imageio-ffmpeg: {e}")
                    self.ffmpeg_path = None
                    self.ffprobe_path = None
            else:
                logger.error(f"❌ Nenhum FFmpeg disponível (imageio-ffmpeg não instalado)")
                self.ffmpeg_path = None
                self.ffprobe_path = None
        
        # Check for whisper.cpp (real C++ implementation) first
        whisper_cpp_dir = os.path.join(backend_root, 'tools', 'whisper_cpp')
        self.whisper_cpp_path = os.path.join(whisper_cpp_dir, 'main')  # whisper.cpp binary is called 'main'
        
        if os.path.exists(self.whisper_cpp_path) and os.access(self.whisper_cpp_path, os.X_OK):
            logger.info(f"✅ whisper.cpp encontrado: {self.whisper_cpp_path}")
            self.whisper_cpp_available = True
        else:
            logger.warning(f"❌ whisper.cpp não encontrado: {self.whisper_cpp_path}")
            self.whisper_cpp_available = False
        
        # Check for OpenAI Whisper CLI as secondary option
        try:
            result = subprocess.run([self.whisper_path, '--help'], 
                                  capture_output=True, text=True, timeout=5)
            logger.info(f"✅ OpenAI Whisper CLI encontrado: {self.whisper_path}")
            self.openai_cli_available = True
        except FileNotFoundError:
            logger.warning(f"❌ OpenAI Whisper CLI não encontrado: {self.whisper_path}")
            self.openai_cli_available = False
        except subprocess.TimeoutExpired:
            logger.info(f"✅ OpenAI Whisper CLI encontrado mas demorou para responder: {self.whisper_path}")
            self.openai_cli_available = True
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar OpenAI Whisper CLI: {e}")
            self.openai_cli_available = False
        
        # Log the transcription options available
        options = []
        if self.whisper_cpp_available:
            options.append("whisper.cpp (C++)")
        if self.openai_cli_available:
            options.append("OpenAI Whisper CLI")
        if self.whisper_python.whisper_available:
            options.append("OpenAI Whisper Python")
        
        if options:
            logger.info(f"🎤 Opções de transcrição disponíveis: {', '.join(options)}")
        else:
            logger.warning("⚠️ Nenhum sistema de transcrição disponível")
    
    async def download_audio(self, url: str) -> Tuple[str, float]:
        """Download audio from YouTube URL and return filepath and duration."""
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'extractaudio': True,
            'audioformat': 'wav',
            'audioquality': 1,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': False,
        }
        
        # Configure FFmpeg for yt-dlp and other tools
        if self.ffmpeg_path:
            ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
            
            # Set FFmpeg location for yt-dlp
            ydl_opts['ffmpeg_location'] = ffmpeg_dir
            
            # Add FFmpeg directory to PATH (for OpenAI Whisper and other tools)
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path:
                os.environ['PATH'] = f"{ffmpeg_dir}:{current_path}"
                logger.info(f"🔧 FFmpeg adicionado ao PATH: {ffmpeg_dir}")
            
            # Set environment variables
            os.environ['FFMPEG_BINARY'] = self.ffmpeg_path
            if self.ffprobe_path:
                os.environ['FFPROBE_BINARY'] = self.ffprobe_path
                logger.info(f"🔧 Usando FFmpeg local: {self.ffmpeg_path}")
                logger.info(f"🔧 Usando FFprobe local: {self.ffprobe_path}")
            else:
                os.environ['FFPROBE_BINARY'] = self.ffmpeg_path
                logger.info(f"🔧 Usando FFmpeg local (sem ffprobe separado): {self.ffmpeg_path}")
            
            logger.info(f"📂 Diretório FFmpeg configurado: {ffmpeg_dir}")
        
        try:
            logger.info(f"📥 Iniciando download: {url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                duration = info.get('duration', 0)
                title = info.get('title', 'unknown')
                logger.info(f"📁 Título: {title}, Duração: {duration}s")
                
                # Find the downloaded audio file
                audio_file = None
                files_in_dir = os.listdir(temp_dir)
                logger.info(f"📂 Arquivos baixados: {files_in_dir}")
                
                # Look for WAV first (post-processed), then other formats
                for file in files_in_dir:
                    if file.endswith('.wav'):
                        audio_file = os.path.join(temp_dir, file)
                        logger.info(f"🎵 Arquivo WAV encontrado: {audio_file}")
                        break
                
                if not audio_file:
                    # Fallback to other audio formats
                    audio_extensions = ['.m4a', '.webm', '.mp3', '.ogg']
                    for file in files_in_dir:
                        for ext in audio_extensions:
                            if file.endswith(ext):
                                audio_file = os.path.join(temp_dir, file)
                                logger.info(f"🎵 Arquivo de áudio encontrado: {audio_file}")
                                break
                        if audio_file:
                            break
                
                if not audio_file:
                    raise Exception("Audio file not found after download")
                
                return audio_file, duration
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
    
    async def transcribe_audio(self, audio_file: str, language: str = "auto") -> Tuple[str, str]:
        """Transcribe audio file using available transcription method."""
        
        # 1st priority: Try whisper.cpp (real C++ implementation)
        if self.whisper_cpp_available:
            try:
                return await self._transcribe_with_whisper_cpp(audio_file, language)
            except Exception as e:
                logger.warning(f"⚠️ whisper.cpp falhou: {e}")
                logger.info("🔄 Tentando com OpenAI Whisper CLI...")
        
        # 2nd priority: Try OpenAI Whisper CLI
        if self.openai_cli_available:
            try:
                return await self._transcribe_with_openai_cli(audio_file, language)
            except Exception as e:
                logger.warning(f"⚠️ OpenAI Whisper CLI falhou: {e}")
                logger.info("🔄 Tentando com OpenAI Whisper Python...")
        
        # 3rd priority: Fallback to OpenAI Whisper Python library
        if self.whisper_python.whisper_available:
            return await self.whisper_python.transcribe_audio(audio_file, language)
        
        # No transcription method available
        raise Exception("Nenhum sistema de transcrição disponível. Instale whisper.cpp ou OpenAI Whisper")
    
    async def _transcribe_with_whisper_cpp(self, audio_file: str, language: str = "auto") -> Tuple[str, str]:
        """Transcribe using real whisper.cpp (C++ implementation)."""
        # Get model path (relative to backend root)
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(backend_root, 'tools', 'whisper_cpp', 'ggml-base.bin')
        
        # Map language parameter for whisper.cpp
        if language == "auto":
            lang_param = []  # No language parameter = auto detection
        else:
            lang_param = ["-l", language]
        
        # Build command for whisper.cpp
        cmd = [self.whisper_cpp_path, "-m", model_path, "-f", audio_file] + lang_param + ["-oj"]
        
        logger.info(f"🤖 Executando whisper.cpp: {' '.join(cmd)}")
        
        # Set environment to find shared libraries
        env = os.environ.copy()
        whisper_cpp_dir = os.path.dirname(self.whisper_cpp_path)
        env['LD_LIBRARY_PATH'] = f"{whisper_cpp_dir}:{env.get('LD_LIBRARY_PATH', '')}"
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=300,  # 5 minutes timeout
                env=env
            )
            logger.info(f"✅ whisper.cpp executado com sucesso")
            
            # Parse whisper.cpp JSON output
            json_file = audio_file + ".json"
            if os.path.exists(json_file):
                async with aiofiles.open(json_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Extract transcription from whisper.cpp JSON format
                    transcription = ""
                    if 'transcription' in data and isinstance(data['transcription'], list):
                        # whisper.cpp format: list of segments with 'text' field
                        for segment in data['transcription']:
                            if isinstance(segment, dict) and 'text' in segment:
                                transcription += segment['text']
                            else:
                                transcription += str(segment)
                    elif 'text' in data:
                        if isinstance(data['text'], list):
                            transcription = ' '.join(str(item) for item in data['text'])
                        else:
                            transcription = str(data['text'])
                    else:
                        # Try to extract from segments (OpenAI format)
                        if 'segments' in data:
                            for segment in data['segments']:
                                if 'text' in segment:
                                    transcription += str(segment['text'])
                        else:
                            transcription = str(data)
                    
                    # Get detected language from whisper.cpp JSON format
                    detected_language = language  # default
                    if 'result' in data and 'language' in data['result']:
                        detected_language = data['result']['language']
                    elif 'language' in data:
                        detected_language = data['language']
                    
                    # Clean up JSON file
                    os.remove(json_file)
                    
                    return transcription.strip(), detected_language
            else:
                # Fallback: parse stdout if JSON file not found
                return result.stdout.strip(), language
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ whisper.cpp falhou: {e.stderr}")
            raise Exception(f"whisper.cpp error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("whisper.cpp timeout - arquivo muito longo")
    
    async def _transcribe_with_openai_cli(self, audio_file: str, language: str = "auto") -> Tuple[str, str]:
        """Transcribe using OpenAI Whisper CLI (not whisper.cpp)."""
        # Map language parameter
        if language == "auto":
            lang_param = None  # Let whisper auto-detect
        else:
            lang_param = language
        
        # Build command for OpenAI Whisper CLI with optimizations
        cmd = [self.whisper_path, audio_file]
        if lang_param:
            cmd.extend(["--language", lang_param])
        cmd.extend([
            "--output_format", "json",
            "--model", "small",  # Use smaller/faster model instead of default medium
            "--fp16", "False",   # Disable FP16 for CPU compatibility
            "--threads", "4"     # Limit threads for better stability
        ])
        
        # Set output directory to same as audio file
        output_dir = os.path.dirname(audio_file)
        cmd.extend(["--output_dir", output_dir])
        
        logger.info(f"🤖 Executando OpenAI Whisper CLI: {' '.join(cmd)}")
        
        try:
            # Calculate timeout based on audio duration (approximately 1/10 of audio length + 60s base)
            timeout_seconds = max(120, min(600, int(os.path.getsize(audio_file) / 1000000) * 10 + 60))
            logger.info(f"⏱️ Timeout configurado: {timeout_seconds}s")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout_seconds
            )
            logger.info(f"✅ OpenAI Whisper CLI executado com sucesso")
            
            # Find the JSON output file
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            json_file = os.path.join(output_dir, f"{base_name}.json")
            
            if os.path.exists(json_file):
                async with aiofiles.open(json_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Extract text from OpenAI Whisper JSON format
                    if 'text' in data:
                        transcription = data['text'].strip()
                    elif 'segments' in data:
                        # Extract from segments if available
                        transcription = ' '.join(segment.get('text', '') for segment in data['segments']).strip()
                    else:
                        transcription = str(data).strip()
                    
                    detected_language = data.get('language', language)
                    
                    # Clean up JSON file
                    os.remove(json_file)
                    
                    return transcription, detected_language
            else:
                # Fallback: try to find txt file
                txt_file = os.path.join(output_dir, f"{base_name}.txt")
                if os.path.exists(txt_file):
                    async with aiofiles.open(txt_file, 'r') as f:
                        transcription = await f.read()
                        os.remove(txt_file)  # Clean up
                        return transcription.strip(), language
                
                # Last fallback: use stdout
                return result.stdout.strip(), language
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ OpenAI Whisper CLI falhou: {e.stderr}")
            raise Exception(f"OpenAI Whisper CLI error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("OpenAI Whisper CLI timeout - arquivo muito longo")
    
    async def cleanup_temp_file(self, filepath: str):
        """Clean up temporary audio file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                # Also remove the directory if it's empty
                temp_dir = os.path.dirname(filepath)
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def process_youtube_video(self, url: str, language: str = "auto") -> dict:
        """Complete pipeline: download audio and transcribe."""
        audio_file = None
        try:
            # Download audio
            audio_file, duration = await self.download_audio(url)
            
            # Transcribe audio
            transcription, detected_language = await self.transcribe_audio(audio_file, language)
            
            return {
                "transcription": transcription,
                "duration": duration,
                "language": detected_language,
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
        finally:
            # Clean up temporary file
            if audio_file:
                await self.cleanup_temp_file(audio_file)