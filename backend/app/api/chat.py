import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import chat_completion, chat_completion_stream
from app.services.vector_service import build_faiss_index, search_chunks, find_timestamp_for_answer
from app.services.cache_service import load_index_data, cache_get, cache_set

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_doc_context(doc_id: str, user_id: str, query: str, db) -> tuple:
    doc = await db.documents.find_one({"_id": doc_id, "user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc["status"] != "ready":
        raise HTTPException(status_code=400, detail=f"Document is {doc['status']}, not ready")

    chunks, vectors = await load_index_data(doc_id)
    if chunks and vectors is not None:
        index = build_faiss_index(vectors)
        results = await search_chunks(query, chunks, index)
        context = "\n\n".join(text for _, text in results)
    else:
        context = (doc.get("text") or "")[:8000]

    return context, doc.get("transcript_segments")


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db),
):
    cache_key = f"chat:{request.document_id}:{hash(request.message)}"
    cached = await cache_get(cache_key)
    if cached:
        return ChatResponse(**json.loads(cached))

    context, segments = await get_doc_context(request.document_id, current_user, request.message, db)
    answer = await chat_completion(context, request.message, request.history)

    timestamp = find_timestamp_for_answer(answer, segments) if segments else None
    seg_end = None
    if timestamp is not None and segments:
        for seg in segments:
            s = seg["start"] if isinstance(seg, dict) else seg.start
            e = seg["end"] if isinstance(seg, dict) else seg.end
            if s <= timestamp <= e:
                seg_end = e
                break

    result = ChatResponse(answer=answer, timestamp=timestamp, segment_end=seg_end)
    await cache_set(cache_key, result.model_dump_json(), ttl=600)
    return result


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
    db=Depends(get_db),
):
    context, segments = await get_doc_context(request.document_id, current_user, request.message, db)

    async def event_generator():
        full_answer = ""
        async for token in chat_completion_stream(context, request.message, request.history):
            full_answer += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        timestamp = find_timestamp_for_answer(full_answer, segments) if segments else None
        yield f"data: {json.dumps({'done': True, 'timestamp': timestamp})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
