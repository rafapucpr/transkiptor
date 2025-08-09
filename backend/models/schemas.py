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


class AudioTranscriptionRequest(BaseModel):
    language: Optional[str] = "auto"
    output_format: str = "txt"  # txt or srt


class AudioTranscriptionResponse(BaseModel):
    transcription: str
    duration: float
    language: str
    success: bool
    output_format: str
    filename: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    success: bool = False