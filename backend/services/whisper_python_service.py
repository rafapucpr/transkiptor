import os
import subprocess
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class WhisperPythonService:
    """Alternative service using OpenAI Whisper Python library."""
    
    def __init__(self):
        self._check_whisper()
    
    def _check_whisper(self):
        """Check if OpenAI Whisper is available."""
        try:
            import whisper
            logger.info("✅ OpenAI Whisper encontrado")
            self.whisper_available = True
        except ImportError:
            logger.warning("❌ OpenAI Whisper não encontrado. Execute: pip install openai-whisper")
            self.whisper_available = False
    
    async def transcribe_audio(self, audio_file: str, language: str = "auto") -> Tuple[str, str]:
        """Transcribe audio using OpenAI Whisper Python library."""
        if not self.whisper_available:
            try:
                import whisper
                self.whisper_available = True
            except ImportError:
                raise Exception("OpenAI Whisper não está instalado. Execute: pip install openai-whisper")
        
        try:
            import whisper
            
            # Ensure local FFmpeg is in PATH if available
            self._ensure_ffmpeg_in_path()
            
            logger.info(f"🤖 Carregando modelo Whisper...")
            
            # Use o modelo base para um bom equilíbrio entre velocidade e qualidade
            model = whisper.load_model("base")
            
            # Configurar idioma
            language_param = None if language == "auto" else language
            
            logger.info(f"🎤 Transcrevendo áudio: {os.path.basename(audio_file)}")
            
            # Transcrever
            result = model.transcribe(
                audio_file,
                language=language_param,
                verbose=False
            )
            
            transcription = result["text"].strip()
            detected_language = result.get("language", language)
            
            logger.info(f"✅ Transcrição concluída. Idioma detectado: {detected_language}")
            logger.info(f"📝 Preview: {transcription[:100]}...")
            
            return transcription, detected_language
            
        except Exception as e:
            logger.error(f"❌ Erro na transcrição: {e}")
            raise Exception(f"Erro na transcrição com OpenAI Whisper: {str(e)}")
    
    def _ensure_ffmpeg_in_path(self):
        """Ensure local FFmpeg is available in PATH."""
        import os
        
        # Check if we have local FFmpeg
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffmpeg_dir = os.path.join(project_root, 'tools', 'ffmpeg')
        ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg')
        
        if os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
            # Add to PATH if not already there
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path:
                os.environ['PATH'] = f"{ffmpeg_dir}:{current_path}"
                logger.info(f"🔧 FFmpeg local adicionado ao PATH para Whisper: {ffmpeg_dir}")
        else:
            logger.warning(f"⚠️ FFmpeg local não encontrado para Whisper: {ffmpeg_path}")