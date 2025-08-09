import os
import tempfile
import subprocess
import json
import logging
import shutil
from typing import Tuple, Optional
import aiofiles
from fastapi import UploadFile
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


class AudioService:
    """Service for processing uploaded audio files."""
    
    def __init__(self):
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
        self.whisper_cpp_path = os.path.join(whisper_cpp_dir, 'main')
        
        if os.path.exists(self.whisper_cpp_path) and os.access(self.whisper_cpp_path, os.X_OK):
            logger.info(f"✅ whisper.cpp encontrado: {self.whisper_cpp_path}")
            self.whisper_cpp_available = True
        else:
            logger.warning(f"❌ whisper.cpp não encontrado: {self.whisper_cpp_path}")
            self.whisper_cpp_available = False
        
        # Log the transcription options available
        options = []
        if self.whisper_cpp_available:
            options.append("whisper.cpp (C++)")
        if self.whisper_python.whisper_available:
            options.append("OpenAI Whisper Python")
        
        if options:
            logger.info(f"🎤 Opções de transcrição disponíveis: {', '.join(options)}")
        else:
            logger.warning("⚠️ Nenhum sistema de transcrição disponível")
    
    async def save_uploaded_file(self, file: UploadFile) -> Tuple[str, float]:
        """Save uploaded audio file and return filepath and duration."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Get file extension
        if file.filename:
            _, ext = os.path.splitext(file.filename)
        else:
            ext = '.wav'  # default extension
        
        # Save uploaded file
        temp_file_path = os.path.join(temp_dir, f"uploaded_audio{ext}")
        
        try:
            async with aiofiles.open(temp_file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"📁 Arquivo salvo: {temp_file_path}")
            
            # Get audio duration
            duration = await self._get_audio_duration(temp_file_path)
            
            # Convert to WAV if needed
            wav_file_path = await self._convert_to_wav(temp_file_path)
            
            # Remove original file if conversion was done
            if wav_file_path != temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return wav_file_path, duration
            
        except Exception as e:
            # Clean up on error
            self._cleanup_temp_dir(temp_dir)
            raise Exception(f"Erro ao processar arquivo: {str(e)}")
    
    async def _get_audio_duration(self, audio_file: str) -> float:
        """Get audio file duration using FFprobe."""
        if not self.ffmpeg_path:
            return 0.0
        
        try:
            probe_cmd = self.ffprobe_path if self.ffprobe_path else self.ffmpeg_path
            cmd = [
                probe_cmd, "-v", "quiet", "-show_entries", 
                "format=duration", "-of", "csv=p=0", audio_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter duração do áudio: {e}")
        
        return 0.0
    
    async def _convert_to_wav(self, input_file: str) -> str:
        """Convert audio file to WAV format if needed."""
        if not self.ffmpeg_path:
            return input_file
        
        # Check if already WAV
        if input_file.lower().endswith('.wav'):
            return input_file
        
        # Convert to WAV
        wav_file = os.path.splitext(input_file)[0] + '_converted.wav'
        
        try:
            cmd = [
                self.ffmpeg_path, "-i", input_file, "-acodec", "pcm_s16le", 
                "-ar", "16000", "-ac", "1", wav_file, "-y"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                logger.info(f"🔄 Arquivo convertido para WAV: {wav_file}")
                return wav_file
            else:
                logger.warning(f"⚠️ Erro na conversão para WAV: {result.stderr}")
                return input_file
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na conversão para WAV: {e}")
            return input_file
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def transcribe_audio(self, audio_file: str, language: str = "auto") -> Tuple[str, str]:
        """Transcribe audio file using available transcription method."""
        
        # 1st priority: Try whisper.cpp (real C++ implementation)
        if self.whisper_cpp_available:
            try:
                transcription, detected_language, _ = await self._transcribe_with_whisper_cpp(audio_file, language, with_timestamps=False)
                return transcription, detected_language
            except Exception as e:
                logger.warning(f"⚠️ whisper.cpp falhou: {e}")
                logger.info("🔄 Tentando com OpenAI Whisper Python...")
        
        # 2nd priority: Fallback to OpenAI Whisper Python library
        if self.whisper_python.whisper_available:
            return await self.whisper_python.transcribe_audio(audio_file, language)
        
        # No transcription method available
        raise Exception("Nenhum sistema de transcrição disponível. Instale whisper.cpp ou OpenAI Whisper")
    
    async def _transcribe_with_whisper_cpp(self, audio_file: str, language: str = "auto", with_timestamps: bool = False) -> Tuple[str, str, Optional[list]]:
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
        base_cmd = [self.whisper_cpp_path, "-m", model_path, "-f", audio_file] + lang_param
        if with_timestamps:
            # Generate both JSON and SRT for timestamps
            cmd = base_cmd + ["-oj", "-osrt"]
        else:
            cmd = base_cmd + ["-oj"]
        
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
            
            # Parse whisper.cpp output
            json_file = audio_file + ".json"
            srt_file = audio_file + ".srt"
            
            # If we requested timestamps and SRT file exists, use it for precise timestamps
            if with_timestamps and os.path.exists(srt_file):
                try:
                    segments = await self._parse_srt_file(srt_file)
                    transcription = " ".join(segment['text'] for segment in segments)
                    
                    # Get language from JSON if available
                    detected_language = language
                    if os.path.exists(json_file):
                        async with aiofiles.open(json_file, 'r') as f:
                            content = await f.read()
                            data = json.loads(content)
                            if 'result' in data and 'language' in data['result']:
                                detected_language = data['result']['language']
                            elif 'language' in data:
                                detected_language = data['language']
                    
                    # Clean up files
                    if os.path.exists(json_file):
                        os.remove(json_file)
                    os.remove(srt_file)
                    
                    return transcription.strip(), detected_language, segments
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar arquivo SRT: {e}")
                    # Fall back to JSON processing
            
            if os.path.exists(json_file):
                async with aiofiles.open(json_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Debug: Log the structure of the JSON data
                    logger.info(f"🐛 Debug - Estrutura do JSON whisper.cpp: {list(data.keys())}")
                    if 'transcription' in data:
                        logger.info(f"🐛 Debug - Tipo de 'transcription': {type(data['transcription'])}")
                        if isinstance(data['transcription'], list) and len(data['transcription']) > 0:
                            logger.info(f"🐛 Debug - Primeiro elemento transcription: {data['transcription'][0]}")
                    if 'segments' in data:
                        logger.info(f"🐛 Debug - Tipo de 'segments': {type(data['segments'])}")
                        if isinstance(data['segments'], list) and len(data['segments']) > 0:
                            logger.info(f"🐛 Debug - Primeiro elemento segments: {data['segments'][0]}")
                    
                    # Extract transcription and segments from whisper.cpp JSON format
                    transcription = ""
                    segments = []
                    
                    if 'transcription' in data and isinstance(data['transcription'], list):
                        # whisper.cpp format: list of segments with 'text' field
                        for segment in data['transcription']:
                            if isinstance(segment, dict) and 'text' in segment:
                                text = segment['text'].strip()
                                transcription += text
                                if with_timestamps and text:
                                    segments.append({
                                        'start': segment.get('start', 0),
                                        'end': segment.get('end', 0),
                                        'text': text
                                    })
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
                                    text = str(segment['text']).strip()
                                    transcription += text
                                    if with_timestamps and text:
                                        segments.append({
                                            'start': segment.get('start', 0),
                                            'end': segment.get('end', 0),
                                            'text': text
                                        })
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
                    
                    return transcription.strip(), detected_language, segments if with_timestamps else None
            else:
                # Fallback: parse stdout if JSON file not found
                return result.stdout.strip(), language, None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ whisper.cpp falhou: {e.stderr}")
            raise Exception(f"whisper.cpp error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("whisper.cpp timeout - arquivo muito longo")
    
    def _format_srt_timestamps(self, segments: list) -> str:
        """Format segments into SRT subtitle format."""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            if not text:
                continue
                
            # Convert seconds to SRT timestamp format (HH:MM:SS,mmm)
            start_time = self._seconds_to_srt_time(start)
            end_time = self._seconds_to_srt_time(end)
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
        
        return srt_content.strip()
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    async def _parse_srt_file(self, srt_file: str) -> list:
        """Parse SRT file generated by whisper.cpp to extract segments with timestamps."""
        segments = []
        
        async with aiofiles.open(srt_file, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Parse SRT format
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # lines[0] = sequence number
                # lines[1] = timestamp
                # lines[2+] = text
                timestamp_line = lines[1]
                text = ' '.join(lines[2:])
                
                # Parse timestamp: "00:00:01,234 --> 00:00:04,567"
                if ' --> ' in timestamp_line:
                    start_str, end_str = timestamp_line.split(' --> ')
                    start_seconds = self._srt_time_to_seconds(start_str)
                    end_seconds = self._srt_time_to_seconds(end_str)
                    
                    segments.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text.strip()
                    })
        
        return segments
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """Convert SRT timestamp format (HH:MM:SS,mmm) to seconds."""
        try:
            # Format: "00:01:23,456"
            time_part, milliseconds = time_str.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + int(milliseconds) / 1000.0
            return total_seconds
        except:
            return 0.0
    
    async def transcribe_audio_with_timestamps(self, audio_file: str, language: str = "auto") -> Tuple[str, str, list]:
        """Transcribe audio and return text, language, and segments with timestamps."""
        
        # 1st priority: Try whisper.cpp with timestamps
        if self.whisper_cpp_available:
            try:
                transcription, detected_language, segments = await self._transcribe_with_whisper_cpp(audio_file, language, with_timestamps=True)
                if segments:
                    return transcription, detected_language, segments
            except Exception as e:
                logger.warning(f"⚠️ whisper.cpp com timestamps falhou: {e}")
                logger.info("🔄 Tentando com OpenAI Whisper Python...")
        
        # 2nd priority: Try OpenAI Whisper Python with timestamps
        if self.whisper_python.whisper_available:
            try:
                return await self.whisper_python.transcribe_audio_with_timestamps(audio_file, language)
            except Exception as e:
                logger.warning(f"⚠️ OpenAI Whisper com timestamps falhou: {e}")
        
        # Fallback: Use regular transcription and create estimated timestamps
        transcription, detected_language = await self.transcribe_audio(audio_file, language)
        
        # Create simple segments for SRT (split by sentences/lines)
        lines = [line.strip() for line in transcription.split('\n') if line.strip()]
        segments = []
        
        # Estimate duration per segment
        duration = await self._get_audio_duration(audio_file)
        if len(lines) > 0:
            segment_duration = duration / len(lines)
            
            for i, line in enumerate(lines):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': line
                })
        
        return transcription, detected_language, segments
    
    async def cleanup_temp_file(self, filepath: str):
        """Clean up temporary audio file."""
        try:
            if os.path.exists(filepath):
                temp_dir = os.path.dirname(filepath)
                self._cleanup_temp_dir(temp_dir)
        except Exception:
            pass  # Ignore cleanup errors
    
    async def process_audio_file(self, file: UploadFile, language: str = "auto", output_format: str = "txt") -> dict:
        """Complete pipeline: save, process and transcribe audio file."""
        audio_file = None
        try:
            # Save uploaded file
            audio_file, duration = await self.save_uploaded_file(file)
            
            # Transcribe audio with or without timestamps
            if output_format == "srt":
                transcription, detected_language, segments = await self.transcribe_audio_with_timestamps(audio_file, language)
                formatted_output = self._format_srt_timestamps(segments)
            else:
                transcription, detected_language = await self.transcribe_audio(audio_file, language)
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
            # Clean up temporary file
            if audio_file:
                await self.cleanup_temp_file(audio_file)