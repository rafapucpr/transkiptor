import os
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from models.schemas import VideoDownloadRequest, ErrorResponse
from services.youtube_download_service import VideoDownloadService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
download_service = VideoDownloadService()


@router.post("/download-youtube",
    summary="Download YouTube Video",
    description="Download high-quality video file from YouTube URL",
    response_description="Video file as download (MP4 format)",
    tags=["YouTube Download"]
)
async def download_video(request: VideoDownloadRequest):
    """
    **Download YouTube Video**
    
    Downloads high-quality video file from YouTube URL using yt-dlp.
    
    **Quality Selection:**
    - Prioritizes 1080p (Full HD) when available
    - Falls back to best available quality (720p, 480p, 360p)
    - MP4 format with H.264 codec for maximum compatibility
    - Includes audio track (AAC codec)
    
    **Process:**
    1. Validate YouTube URL format
    2. Extract video metadata (title, duration, etc.)
    3. Download best quality video + audio
    4. Merge streams if necessary
    5. Return as downloadable file
    
    **Supported URLs:**
    - Standard YouTube: `https://www.youtube.com/watch?v=VIDEO_ID`
    - Short URLs: `https://youtu.be/VIDEO_ID`
    - YouTube Music: `https://music.youtube.com/watch?v=VIDEO_ID`
    - Playlist URLs: Downloads first video only
    
    **Parameters:**
    - **url**: YouTube video URL (required)
    
    **Returns:**
    Video file download with headers:
    - **Content-Type**: `video/mp4`
    - **Content-Disposition**: `attachment; filename="video_title.mp4"`
    - **Content-Length**: File size in bytes
    
    **File Naming:**
    - Uses sanitized video title as filename
    - Removes special characters and emojis
    - Adds `.mp4` extension
    - Example: `"Amazing Video Title.mp4"`
    
    **Features:**
    - High-quality downloads (up to 1080p)
    - Fast processing with parallel downloads
    - Automatic stream merging when needed
    - Error handling for private/restricted videos
    - Cleanup of temporary files
    
    **Limitations:**
    - Public videos only
    - No age-restricted content
    - Maximum file size: ~2GB (typical 1-2 hour videos)
    - Geographic restrictions may apply
    - Premium/paid content not supported
    
    **Example Usage:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/download" \\
         -H "Content-Type: application/json" \\
         -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \\
         --output video.mp4
    ```
    
    **Common Errors:**
    - `400`: Invalid URL format
    - `404`: Video not found or private
    - `403`: Geographic restrictions or age-restricted
    - `500`: Download or processing error
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