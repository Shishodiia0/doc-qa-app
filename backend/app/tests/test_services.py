import pytest
import numpy as np
from unittest.mock import MagicMock, patch, mock_open, AsyncMock
from app.services.document_service import (
    extract_pdf_text, transcribe_audio_video, generate_summary,
    chunk_text, segments_to_text,
)
from app.services.vector_service import embed_texts, build_faiss_index, search_chunks, find_timestamp_for_answer
from app.services.cache_service import cache_get, cache_set, cache_delete, store_index_data, load_index_data
from app.models.schemas import TranscriptSegment


# ── document_service ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_extract_pdf_text():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Hello PDF"
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]
    with patch("app.services.document_service.pdfplumber.open", return_value=mock_pdf):
        text = await extract_pdf_text("/fake/path.pdf")
    assert text == "Hello PDF"


@pytest.mark.asyncio
async def test_extract_pdf_text_multiple_pages():
    pages = [MagicMock(extract_text=MagicMock(return_value=f"Page {i}")) for i in range(3)]
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = pages
    with patch("app.services.document_service.pdfplumber.open", return_value=mock_pdf):
        text = await extract_pdf_text("/fake/path.pdf")
    assert "Page 0" in text and "Page 2" in text


@pytest.mark.asyncio
async def test_extract_pdf_empty_pages():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None
    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]
    with patch("app.services.document_service.pdfplumber.open", return_value=mock_pdf):
        text = await extract_pdf_text("/fake/path.pdf")
    assert text == ""


@pytest.mark.asyncio
async def test_transcribe_audio_video():
    mock_seg = MagicMock()
    mock_seg.get = lambda k, d=None: {"start": 0.0, "end": 5.0, "text": "Hello world"}.get(k, d)
    mock_response = MagicMock()
    mock_response.segments = [mock_seg]
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
    with patch("app.services.document_service.client", mock_client), \
         patch("builtins.open", mock_open(read_data=b"audio")):
        segments = await transcribe_audio_video("/fake/audio.mp3")
    assert len(segments) == 1
    assert segments[0].start == 0.0


@pytest.mark.asyncio
async def test_transcribe_empty_segments():
    mock_response = MagicMock()
    mock_response.segments = []
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
    with patch("app.services.document_service.client", mock_client), \
         patch("builtins.open", mock_open(read_data=b"audio")):
        segments = await transcribe_audio_video("/fake/audio.mp3")
    assert segments == []


@pytest.mark.asyncio
async def test_generate_summary():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is a summary."
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    with patch("app.services.document_service.client", mock_client):
        summary = await generate_summary("Long document text here...")
    assert summary == "This is a summary."


def test_chunk_text_basic():
    text = " ".join([f"word{i}" for i in range(1000)])
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)


def test_chunk_text_short():
    text = "short text"
    chunks = chunk_text(text, chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_text_overlap():
    words = [f"w{i}" for i in range(20)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=10, overlap=5)
    assert len(chunks) >= 2


def test_segments_to_text():
    segs = [
        TranscriptSegment(start=0, end=5, text="Hello"),
        TranscriptSegment(start=5, end=10, text="world"),
    ]
    result = segments_to_text(segs)
    assert result == "Hello world"


def test_segments_to_text_empty():
    assert segments_to_text([]) == ""


# ── vector_service ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_embed_texts():
    vectors = await embed_texts(["test text"])
    assert vectors.shape == (1, 256)


def test_build_faiss_index():
    vectors = np.random.rand(5, 256).astype(np.float32)
    index = build_faiss_index(vectors)
    assert index.ntotal == 5


@pytest.mark.asyncio
async def test_search_chunks():
    chunks = ["chunk one about AI", "chunk two about ML", "chunk three about data"]
    vectors = await embed_texts(chunks)
    index = build_faiss_index(vectors)
    results = await search_chunks("AI query", chunks, index, top_k=2)
    assert len(results) <= 2
    assert all(isinstance(r[1], str) for r in results)


@pytest.mark.asyncio
async def test_search_chunks_fewer_than_topk():
    chunks = ["only one chunk"]
    vectors = await embed_texts(chunks)
    index = build_faiss_index(vectors)
    results = await search_chunks("query", chunks, index, top_k=10)
    assert len(results) == 1


def test_find_timestamp_no_segments():
    assert find_timestamp_for_answer("some answer", None) is None
    assert find_timestamp_for_answer("some answer", []) is None


def test_find_timestamp_match():
    segs = [
        TranscriptSegment(start=0.0, end=5.0, text="introduction to python"),
        TranscriptSegment(start=5.0, end=10.0, text="machine learning algorithms"),
    ]
    ts = find_timestamp_for_answer("machine learning algorithms are powerful", segs)
    assert ts == 5.0


def test_find_timestamp_no_match():
    segs = [TranscriptSegment(start=0.0, end=5.0, text="xyz abc def")]
    ts = find_timestamp_for_answer("completely unrelated answer", segs)
    assert ts is None


# ── cache_service ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_set_and_get():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="cached_value")
    mock_redis.setex = AsyncMock()
    with patch("app.services.cache_service.get_redis", AsyncMock(return_value=mock_redis)):
        await cache_set("key1", "cached_value", ttl=60)
        result = await cache_get("key1")
    assert result == "cached_value"


@pytest.mark.asyncio
async def test_cache_get_miss():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    with patch("app.services.cache_service.get_redis", AsyncMock(return_value=mock_redis)):
        result = await cache_get("missing_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    mock_redis = AsyncMock()
    mock_redis.delete = AsyncMock()
    with patch("app.services.cache_service.get_redis", AsyncMock(return_value=mock_redis)):
        await cache_delete("key1")
    mock_redis.delete.assert_called_once_with("key1")


@pytest.mark.asyncio
async def test_store_and_load_index_data():
    chunks = ["chunk1", "chunk2"]
    vectors = np.random.rand(2, 256).astype(np.float32)
    stored = {}

    async def fake_setex(key, ttl, val):
        stored[key] = val

    async def fake_get(key):
        return stored.get(key)

    mock_text_redis = AsyncMock()
    mock_text_redis.setex = fake_setex
    mock_text_redis.get = fake_get

    mock_bin_redis = AsyncMock()
    mock_bin_redis.setex = fake_setex
    mock_bin_redis.get = fake_get

    with patch("app.services.cache_service.get_redis", AsyncMock(return_value=mock_text_redis)), \
         patch("app.services.cache_service.get_redis_bytes", AsyncMock(return_value=mock_bin_redis)):
        await store_index_data("doc-1", chunks, vectors.tobytes())
        loaded_chunks, loaded_vectors = await load_index_data("doc-1")

    assert loaded_chunks == chunks
    assert loaded_vectors.shape == (2, 256)


@pytest.mark.asyncio
async def test_load_index_data_missing():
    mock_text_redis = AsyncMock()
    mock_text_redis.get = AsyncMock(return_value=None)
    mock_bin_redis = AsyncMock()
    mock_bin_redis.get = AsyncMock(return_value=None)
    with patch("app.services.cache_service.get_redis", AsyncMock(return_value=mock_text_redis)), \
         patch("app.services.cache_service.get_redis_bytes", AsyncMock(return_value=mock_bin_redis)):
        chunks, vectors = await load_index_data("nonexistent")
    assert chunks is None
    assert vectors is None
