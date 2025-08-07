from fastapi import APIRouter, HTTPException, Depends
from models.schemas import TranscriptionRequest, TranscriptionResponse, ErrorResponse
from services.youtube_service import YouTubeService

router = APIRouter()

def get_youtube_service():
    return YouTubeService()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_video(
    request: TranscriptionRequest,
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """
    Transcribe audio from a YouTube video URL.
    
    - **url**: YouTube video URL
    - **language**: Language code (optional, defaults to auto-detection)
    """
    try:
        result = await youtube_service.process_youtube_video(
            str(request.url), 
            request.language or "auto"
        )
        
        if result["success"]:
            return TranscriptionResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}