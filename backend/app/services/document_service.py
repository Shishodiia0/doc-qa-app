import pdfplumber
from typing import List
from groq import AsyncGroq
from app.core.config import get_settings
from app.models.schemas import TranscriptSegment

settings = get_settings()
client = AsyncGroq(api_key=settings.groq_api_key)
MODEL = "llama-3.1-8b-instant"


async def extract_pdf_text(file_path: str) -> str:
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n\n".join(text_parts)


async def transcribe_audio_video(file_path: str) -> List[TranscriptSegment]:
    with open(file_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )
    segments = []
    for seg in (response.segments or []):
        segments.append(TranscriptSegment(
            start=float(seg.get("start", 0)),
            end=float(seg.get("end", 0)),
            text=seg.get("text", "").strip(),
        ))
    return segments


async def generate_summary(text: str) -> str:
    truncated = text[:12000]
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Summarize the following document concisely in 3-5 sentences."},
            {"role": "user", "content": truncated},
        ],
        max_tokens=512,
    )
    return response.choices[0].message.content


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def segments_to_text(segments: List[TranscriptSegment]) -> str:
    return " ".join(s.text for s in segments)
