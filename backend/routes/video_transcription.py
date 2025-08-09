from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response
from models.schemas import AudioTranscriptionResponse, ErrorResponse
from services.video_service import VideoService
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_video_service():
    return VideoService()


@router.post("/transcribe-video", 
    response_model=AudioTranscriptionResponse,
    summary="Transcribe Video File",
    description="Extract audio from video file and transcribe it using whisper.cpp or OpenAI Whisper",
    response_description="Transcription result with metadata",
    tags=["Video Transcription"]
)
async def transcribe_video_file(
    file: UploadFile = File(..., description="Video file to transcribe (max 5GB)"),
    language: Optional[str] = Form("auto", description="Language code: 'auto', 'pt', 'en', 'es', 'fr', 'de', 'it'"),
    output_format: Optional[str] = Form("txt", description="Output format: 'txt' for plain text or 'srt' for subtitles with timestamps"),
    video_service: VideoService = Depends(get_video_service)
):
    """
    **Transcribe Video File**
    
    Extracts audio from uploaded video file and transcribes it to text or SRT subtitles.
    
    **Supported Video Formats:**
    - MP4, AVI, MOV, MKV, WEBM, FLV, WMV, M4V, 3GP, OGV
    
    **Process:**
    1. Upload video file (up to 5GB)
    2. Extract audio using FFmpeg
    3. Transcribe audio using whisper.cpp or OpenAI Whisper
    4. Return transcription with metadata
    
    **Parameters:**
    - **file**: Video file to process (required)
    - **language**: Target language for transcription
        - "auto": Automatic language detection (default)
        - "pt": Portuguese
        - "en": English  
        - "es": Spanish
        - "fr": French
        - "de": German
        - "it": Italian
    - **output_format**: Format of transcription output
        - "txt": Plain text (default)
        - "srt": SRT subtitles with timestamps
    
    **Returns:**
    - **transcription**: Transcribed text or SRT content
    - **duration**: Video duration in seconds
    - **language**: Detected or specified language
    - **output_format**: Format used for output
    - **filename**: Original filename
    - **success**: Operation status
    
    **Limitations:**
    - Maximum file size: 5GB
    - Supported formats only
    - Processing timeout: 10 minutes
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado")
    
    # Check file extension
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.ogv']
    file_ext = file.filename.lower()
    if not any(file_ext.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Formato de arquivo não suportado. Use um dos seguintes: {', '.join(allowed_extensions)}"
        )
    
    # Validate output format
    if output_format not in ["txt", "srt"]:
        raise HTTPException(status_code=400, detail="Formato de saída deve ser 'txt' ou 'srt'")
    
    # Check file size (limit to 5GB for videos)
    max_size = 5 * 1024 * 1024 * 1024  # 5GB in bytes
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Limite de 5GB")
    
    logger.info(f"📹 Recebido vídeo: {file.filename} ({file_size / 1024 / 1024:.1f}MB)")
    
    try:
        result = await video_service.process_video_file(
            file=file,
            language=language or "auto",
            output_format=output_format or "txt"
        )
        
        if result["success"]:
            return AudioTranscriptionResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"❌ Erro na transcrição do vídeo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe-video/download",
    summary="Transcribe Video and Download Result",
    description="Extract audio from video file, transcribe it, and return transcription as downloadable file",
    response_description="Downloadable transcription file (.txt or .srt)",
    tags=["Video Transcription"]
)
async def download_video_transcription(
    file: UploadFile = File(..., description="Video file to transcribe (max 5GB)"),
    language: Optional[str] = Form("auto", description="Language code: 'auto', 'pt', 'en', 'es', 'fr', 'de', 'it'"),
    output_format: Optional[str] = Form("txt", description="Output format: 'txt' for plain text or 'srt' for subtitles with timestamps"),
    video_service: VideoService = Depends(get_video_service)
):
    """
    **Transcribe Video File and Download**
    
    Processes video file and returns transcription as downloadable file.
    
    **Features:**
    - Direct file download (no JSON response)
    - Automatic filename generation
    - Proper content-type headers
    - Original filename preservation
    
    **Process:**
    1. Upload video file
    2. Extract audio using FFmpeg
    3. Transcribe using whisper.cpp or OpenAI Whisper
    4. Format as TXT or SRT
    5. Return as downloadable file
    
    **Parameters:**
    Same as `/transcribe-video` endpoint
    
    **Returns:**
    Downloadable file with transcription:
    - **Content-Type**: `text/plain` (TXT) or `application/x-subrip` (SRT)
    - **Content-Disposition**: `attachment; filename="original_name_transcription.{format}"`
    
    **Example Usage:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/transcribe-video/download" \\
         -F "file=@video.mp4" \\
         -F "language=pt" \\
         -F "output_format=srt" \\
         --output transcricao.srt
    ```
    """
    # Use the same validation and processing as the regular endpoint
    result = await transcribe_video_file(file, language, output_format, video_service)
    
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
    return {"status": "healthy", "service": "video_transcription"}