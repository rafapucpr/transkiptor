from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routes.transcription import router as transcription_router
from routes.download import router as download_router
from routes.audio_transcription import router as audio_transcription_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Transkiptor API",
    description="API para transcrição de vídeos do YouTube usando yt-dlp e whisper.cpp",
    version="1.0.0"
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

app.include_router(transcription_router, prefix="/api/v1", tags=["transcription"])
app.include_router(download_router, prefix="/api/v1", tags=["download"])
app.include_router(audio_transcription_router, prefix="/api/v1", tags=["audio-transcription"])


@app.get("/")
async def root():
    return {
        "message": "Transkiptor API", 
        "version": "1.0.0",
        "docs": "/docs"
    }