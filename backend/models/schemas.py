from pydantic import BaseModel, HttpUrl
from typing import Optional


class TranscriptionRequest(BaseModel):
    url: HttpUrl
    language: Optional[str] = "auto"


class VideoDownloadRequest(BaseModel):
    url: HttpUrl


class TranscriptionResponse(BaseModel):
    transcription: str
    duration: float
    language: str
    success: bool


class ErrorResponse(BaseModel):
    error: str
    success: bool = False