import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from .conftest import auth_headers, mock_doc


def make_vectors():
    return np.random.rand(1, 1536).astype(np.float32)


# ── chat ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_success(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())
    with patch("app.api.chat.load_index_data", AsyncMock(return_value=(None, None))), \
         patch("app.api.chat.cache_get", AsyncMock(return_value=None)), \
         patch("app.api.chat.cache_set", AsyncMock()), \
         patch("app.api.chat.chat_completion", AsyncMock(return_value="Machine learning is a subset of AI.")):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "doc-1", "message": "What is ML?", "history": []},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["answer"] == "Machine learning is a subset of AI."


@pytest.mark.asyncio
async def test_chat_returns_cached(client, mock_db):
    cached = json.dumps({"answer": "cached answer", "timestamp": None, "segment_end": None})
    with patch("app.api.chat.cache_get", AsyncMock(return_value=cached)):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "doc-1", "message": "What is ML?"},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "cached answer"


@pytest.mark.asyncio
async def test_chat_document_not_found(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=None)
    with patch("app.api.chat.cache_get", AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "missing", "message": "hello"},
            headers=auth_headers(),
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_document_not_ready(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc({"status": "processing"}))
    with patch("app.api.chat.cache_get", AsyncMock(return_value=None)):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "doc-1", "message": "hello"},
            headers=auth_headers(),
        )
    assert resp.status_code == 400
    assert "processing" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_chat_with_vector_search(client, mock_db):
    chunks = ["chunk about ML", "chunk about AI"]
    vectors = make_vectors()
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())
    with patch("app.api.chat.load_index_data", AsyncMock(return_value=(chunks, vectors))), \
         patch("app.api.chat.cache_get", AsyncMock(return_value=None)), \
         patch("app.api.chat.cache_set", AsyncMock()), \
         patch("app.api.chat.build_faiss_index", return_value=MagicMock()), \
         patch("app.api.chat.search_chunks", AsyncMock(return_value=[(0, "chunk about ML")])), \
         patch("app.api.chat.chat_completion", AsyncMock(return_value="ML answer")):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "doc-1", "message": "What is ML?"},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    assert resp.json()["answer"] == "ML answer"


@pytest.mark.asyncio
async def test_chat_with_timestamp(client, mock_db):
    segments = [{"start": 10.0, "end": 20.0, "text": "machine learning is great"}]
    doc = mock_doc({"transcript_segments": segments, "file_type": "audio"})
    mock_db.documents.find_one = AsyncMock(return_value=doc)
    with patch("app.api.chat.load_index_data", AsyncMock(return_value=(None, None))), \
         patch("app.api.chat.cache_get", AsyncMock(return_value=None)), \
         patch("app.api.chat.cache_set", AsyncMock()), \
         patch("app.api.chat.chat_completion", AsyncMock(return_value="machine learning is great")):
        resp = await client.post(
            "/api/v1/chat/",
            json={"document_id": "doc-1", "message": "Tell me about ML"},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["timestamp"] == 10.0
    assert data["segment_end"] == 20.0


@pytest.mark.asyncio
async def test_chat_no_auth(client):
    resp = await client.post("/api/v1/chat/", json={"document_id": "d1", "message": "hi"})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_chat_stream_success(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())

    async def fake_stream(*args, **kwargs):
        for token in ["Hello", " world"]:
            yield token

    with patch("app.api.chat.load_index_data", AsyncMock(return_value=(None, None))), \
         patch("app.api.chat.chat_completion_stream", fake_stream):
        resp = await client.post(
            "/api/v1/chat/stream",
            json={"document_id": "doc-1", "message": "hi"},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
