from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.transcription import router as transcription_router
from routes.download import router as download_router

app = FastAPI(
    title="Transkiptor API",
    description="API para transcrição de vídeos do YouTube usando yt-dlp e whisper.cpp",
    version="1.0.0"
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


@app.get("/")
async def root():
    return {
        "message": "Transkiptor API", 
        "version": "1.0.0",
        "docs": "/docs"
    }