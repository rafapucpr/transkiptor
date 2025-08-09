from fastapi import APIRouter, HTTPException, Depends
from models.schemas import TranscriptionRequest, TranscriptionResponse, ErrorResponse
from services.youtube_service import YouTubeService

router = APIRouter()

def get_youtube_service():
    return YouTubeService()


@router.post("/transcribe-youtube", 
    response_model=TranscriptionResponse,
    summary="Transcribe YouTube Video",
    description="Download audio from YouTube video and transcribe it using AI models",
    response_description="Transcription result with metadata",
    tags=["YouTube Transcription"]
)
async def transcribe_video(
    request: TranscriptionRequest,
    youtube_service: YouTubeService = Depends(get_youtube_service)
):
    """
    **Transcribe YouTube Video Audio**
    
    Downloads audio from YouTube video and transcribes it to text using advanced AI models.
    
    **Process:**
    1. Validate YouTube URL
    2. Download audio using yt-dlp (best quality available)
    3. Convert audio to optimal format for transcription
    4. Transcribe using whisper.cpp or OpenAI Whisper
    5. Return transcription with metadata
    
    **Supported URLs:**
    - Standard YouTube URLs: `https://www.youtube.com/watch?v=VIDEO_ID`
    - Short YouTube URLs: `https://youtu.be/VIDEO_ID`
    - YouTube Music: `https://music.youtube.com/watch?v=VIDEO_ID`
    - Playlist URLs (processes first video): `https://www.youtube.com/playlist?list=PLAYLIST_ID`
    
    **Parameters:**
    - **url**: YouTube video URL (required)
    - **language**: Target language for transcription (optional)
        - "auto": Automatic language detection (default)
        - "pt": Portuguese
        - "en": English
        - "es": Spanish
        - "fr": French
        - "de": German
        - "it": Italian
    
    **Returns:**
    - **transcription**: Complete transcribed text
    - **duration**: Video duration in seconds
    - **language**: Detected or specified language
    - **success**: Operation status
    
    **Features:**
    - High-quality audio extraction (best available format)
    - Intelligent transcription engine selection
    - Multi-language support with auto-detection
    - Automatic cleanup of temporary files
    - Error handling for private/restricted videos
    
    **Limitations:**
    - Public videos only (no private/unlisted)
    - No age-restricted content
    - Maximum video length: 2 hours
    - Geographic restrictions may apply
    
    **Example Request:**
    ```json
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "language": "en"
    }
    ```
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