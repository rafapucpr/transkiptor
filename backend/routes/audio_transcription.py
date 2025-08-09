from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response
from models.schemas import AudioTranscriptionResponse, ErrorResponse
from services.audio_service import AudioService
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_audio_service():
    return AudioService()


@router.post("/transcribe-audio", response_model=AudioTranscriptionResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: Optional[str] = Form("auto"),
    output_format: Optional[str] = Form("txt"),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Transcribe audio from uploaded file.
    
    - **file**: Audio file (supported formats: wav, mp3, m4a, ogg, webm, etc.)
    - **language**: Language code (optional, defaults to auto-detection)
    - **output_format**: Output format - "txt" for plain text or "srt" for subtitles with timestamps
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado")
    
    # Check file extension
    allowed_extensions = ['.wav', '.mp3', '.m4a', '.ogg', '.webm', '.flac', '.aac', '.mp4', '.mov', '.avi']
    file_ext = file.filename.lower()
    if not any(file_ext.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de arquivo não suportado. Use um dos seguintes: {', '.join(allowed_extensions)}"
        )
    
    # Validate output format
    if output_format not in ["txt", "srt"]:
        raise HTTPException(status_code=400, detail="Formato de saída deve ser 'txt' ou 'srt'")
    
    # Check file size (limit to 100MB)
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Limite de 100MB")
    
    logger.info(f"📤 Recebido arquivo: {file.filename} ({file_size / 1024 / 1024:.1f}MB)")
    
    try:
        result = await audio_service.process_audio_file(
            file=file,
            language=language or "auto",
            output_format=output_format or "txt"
        )
        
        if result["success"]:
            return AudioTranscriptionResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"❌ Erro na transcrição: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-audio/download")
async def download_transcription(
    file: UploadFile = File(...),
    language: Optional[str] = Form("auto"),
    output_format: Optional[str] = Form("txt"),
    audio_service: AudioService = Depends(get_audio_service)
):
    """
    Transcribe audio file and return as downloadable file.
    
    - **file**: Audio file (supported formats: wav, mp3, m4a, ogg, webm, etc.)
    - **language**: Language code (optional, defaults to auto-detection)
    - **output_format**: Output format - "txt" for plain text or "srt" for subtitles with timestamps
    """
    # Use the same validation and processing as the regular endpoint
    result = await transcribe_audio_file(file, language, output_format, audio_service)
    
    # Create filename
    original_name = file.filename or "transcription"
    name_without_ext = original_name.rsplit('.', 1)[0]
    download_filename = f"{name_without_ext}_transcription.{output_format}"
    
    # Set appropriate content type
    content_type = "text/plain" if output_format == "txt" else "application/x-subrip"
    
    return Response(
        content=result.transcription,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={download_filename}"}
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "audio_transcription"}