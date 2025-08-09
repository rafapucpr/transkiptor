from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routes.youtube_transcription import router as transcription_router
from routes.youtube_download import router as download_router
from routes.audio_transcription import router as audio_transcription_router
from routes.video_transcription import router as video_transcription_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Transkiptor API",
    description="🎬 Sistema completo de transcrição para YouTube, áudios e vídeos",
    version="2.0.0",
    contact={
        "name": "Transkiptor Support",
        "url": "https://github.com/your-repo/transkiptor",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://your-domain.com",
            "description": "Production server"
        }
    ]
)

# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Dados inválidos fornecidos",
            "errors": exc.errors()
        }
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcription_router, prefix="/api/v1")
app.include_router(download_router, prefix="/api/v1")
app.include_router(audio_transcription_router, prefix="/api/v1")
app.include_router(video_transcription_router, prefix="/api/v1")


@app.get("/",
    summary="API Information",
    description="Get basic information about the Transkiptor API",
    tags=["General"]
)
async def root():
    """
    **API Information**
    
    Returns basic information about the Transkiptor API and available endpoints.
    """
    return {
        "message": "🎬 Transkiptor API", 
        "version": "2.0.0",
        "description": "Sistema completo de transcrição para YouTube, áudios e vídeos",
        "features": {
            "youtube_transcription": "Transcrição de vídeos do YouTube via URL",
            "audio_transcription": "Upload e transcrição de arquivos de áudio (100MB)",
            "video_transcription": "Upload e transcrição de arquivos de vídeo (5GB)",
            "formats": ["txt", "srt"],
            "languages": ["auto", "pt", "en", "es", "fr", "de", "it"]
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc", 
            "openapi": "/openapi.json"
        },
        "status": "running",
        "engines": ["whisper.cpp", "OpenAI Whisper"]
    }