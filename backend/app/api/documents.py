import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import DocumentResponse, FileType
from app.services.document_service import (
    extract_pdf_text, transcribe_audio_video, generate_summary,
    chunk_text, segments_to_text,
)
from app.services.vector_service import embed_texts
from app.services.cache_service import store_index_data

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()

ALLOWED_EXTENSIONS = {
    "pdf": FileType.pdf,
    "mp3": FileType.audio, "wav": FileType.audio, "m4a": FileType.audio,
    "mp4": FileType.video, "mov": FileType.video, "avi": FileType.video, "mkv": FileType.video,
}


def get_file_type(filename: str) -> FileType:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    return ALLOWED_EXTENSIONS[ext]


async def process_document(doc_id: str, file_path: str, file_type: FileType, db):
    try:
        await db.documents.update_one({"_id": doc_id}, {"$set": {"status": "processing"}})

        if file_type == FileType.pdf:
            text = await extract_pdf_text(file_path)
            segments = None
        else:
            segments = await transcribe_audio_video(file_path)
            text = segments_to_text(segments)

        summary = await generate_summary(text)
        chunks = chunk_text(text)
        vectors = await embed_texts(chunks)
        vectors_bytes = vectors.tobytes()
        await store_index_data(doc_id, chunks, vectors_bytes)

        update = {
            "status": "ready",
            "summary": summary,
            "text": text,
            "chunks": chunks,
        }
        if segments:
            update["transcript_segments"] = [s.model_dump() for s in segments]

        await db.documents.update_one({"_id": doc_id}, {"$set": update})
    except Exception as e:
        await db.documents.update_one({"_id": doc_id}, {"$set": {"status": "error", "error": str(e)}})


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db=Depends(get_db),
):
    file_type = get_file_type(file.filename)
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    os.makedirs(settings.upload_dir, exist_ok=True)
    doc_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[-1].lower()
    file_path = os.path.join(settings.upload_dir, f"{doc_id}.{ext}")

    size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)

    doc = {
        "_id": doc_id,
        "filename": file.filename,
        "file_type": file_type.value,
        "user_id": current_user,
        "status": "pending",
        "summary": None,
        "transcript_segments": None,
        "file_path": file_path,
        "created_at": datetime.utcnow(),
    }
    await db.documents.insert_one(doc)
    background_tasks.add_task(process_document, doc_id, file_path, file_type, db)

    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        file_type=file_type,
        user_id=current_user,
        status="pending",
        created_at=doc["created_at"],
        file_path=file_path,
    )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(current_user: str = Depends(get_current_user), db=Depends(get_db)):
    docs = await db.documents.find({"user_id": current_user}).to_list(100)
    return [
        DocumentResponse(
            id=d["_id"], filename=d["filename"], file_type=d["file_type"],
            user_id=d["user_id"], status=d["status"], summary=d.get("summary"),
            transcript_segments=d.get("transcript_segments"),
            created_at=d["created_at"], file_path=d.get("file_path"),
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, current_user: str = Depends(get_current_user), db=Depends(get_db)):
    doc = await db.documents.find_one({"_id": doc_id, "user_id": current_user})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(
        id=doc["_id"], filename=doc["filename"], file_type=doc["file_type"],
        user_id=doc["user_id"], status=doc["status"], summary=doc.get("summary"),
        transcript_segments=doc.get("transcript_segments"),
        created_at=doc["created_at"], file_path=doc.get("file_path"),
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str, current_user: str = Depends(get_current_user), db=Depends(get_db)):
    doc = await db.documents.find_one({"_id": doc_id, "user_id": current_user})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("file_path") and os.path.exists(doc["file_path"]):
        os.remove(doc["file_path"])
    await db.documents.delete_one({"_id": doc_id})


@router.get("/{doc_id}/stream")
async def stream_media(doc_id: str, current_user: str = Depends(get_current_user), db=Depends(get_db)):
    doc = await db.documents.find_one({"_id": doc_id, "user_id": current_user})
    if not doc or not doc.get("file_path"):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(doc["file_path"])
