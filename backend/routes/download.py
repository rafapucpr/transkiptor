import os
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from models.schemas import VideoDownloadRequest, ErrorResponse
from services.video_download_service import VideoDownloadService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
download_service = VideoDownloadService()


@router.post("/download")
async def download_video(request: VideoDownloadRequest):
    """
    Download video from YouTube URL
    """
    try:
        logger.info(f"📥 Iniciando download do vídeo: {request.url}")
        
        # Download video
        video_file, filename, metadata = await download_service.download_video(str(request.url))
        
        # Check if file exists
        if not os.path.exists(video_file):
            raise HTTPException(status_code=500, detail="Arquivo de vídeo não foi encontrado após o download")
        
        # Return file for download with proper headers
        async def cleanup_file():
            """Clean up the temporary file after sending"""
            try:
                if os.path.exists(video_file):
                    os.remove(video_file)
                    # Also remove the directory if it's empty
                    temp_dir = os.path.dirname(video_file)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar arquivo temporário: {e}")
        
        logger.info(f"✅ Download concluído: {filename}")
        
        return FileResponse(
            path=video_file,
            media_type='video/mp4',
            filename=filename,
            background=cleanup_file
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no download do vídeo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )