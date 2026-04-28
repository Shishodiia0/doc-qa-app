from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    pdf = "pdf"
    audio = "audio"
    video = "video"


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: FileType
    user_id: str
    status: str
    summary: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    created_at: datetime
    file_path: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    document_id: str
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    answer: str
    timestamp: Optional[float] = None
    segment_end: Optional[float] = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
