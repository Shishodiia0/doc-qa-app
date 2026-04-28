import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from .conftest import auth_headers, mock_doc


# ── upload ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_pdf_success(client, mock_db):
    with patch("app.api.documents.process_document") as mock_proc, \
         patch("builtins.open", MagicMock()), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=True):
        mock_proc.return_value = None
        content = b"%PDF-1.4 test content"
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(content), "application/pdf")},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "pdf"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_upload_audio_success(client, mock_db):
    with patch("app.api.documents.process_document"), \
         patch("builtins.open", MagicMock()), \
         patch("os.makedirs"):
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("audio.mp3", io.BytesIO(b"fake-audio"), "audio/mpeg")},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    assert resp.json()["file_type"] == "audio"


@pytest.mark.asyncio
async def test_upload_video_success(client, mock_db):
    with patch("app.api.documents.process_document"), \
         patch("builtins.open", MagicMock()), \
         patch("os.makedirs"):
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("video.mp4", io.BytesIO(b"fake-video"), "video/mp4")},
            headers=auth_headers(),
        )
    assert resp.status_code == 200
    assert resp.json()["file_type"] == "video"


@pytest.mark.asyncio
async def test_upload_unsupported_type(client, mock_db):
    with patch("os.makedirs"):
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("file.xyz", io.BytesIO(b"data"), "application/octet-stream")},
            headers=auth_headers(),
        )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_no_auth(client):
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(b"data"), "application/pdf")},
    )
    assert resp.status_code in (401, 403)


# ── list ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_documents_empty(client, mock_db):
    mock_db.documents.find.return_value.to_list = AsyncMock(return_value=[])
    resp = await client.get("/api/v1/documents/", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_documents_with_items(client, mock_db):
    mock_db.documents.find.return_value.to_list = AsyncMock(return_value=[mock_doc()])
    resp = await client.get("/api/v1/documents/", headers=auth_headers())
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["filename"] == "test.pdf"


# ── get ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_document_found(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())
    resp = await client.get("/api/v1/documents/doc-1", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["id"] == "doc-1"


@pytest.mark.asyncio
async def test_get_document_not_found(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=None)
    resp = await client.get("/api/v1/documents/missing", headers=auth_headers())
    assert resp.status_code == 404


# ── delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_document_success(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())
    with patch("os.path.exists", return_value=False):
        resp = await client.delete("/api/v1/documents/doc-1", headers=auth_headers())
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_document_not_found(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=None)
    resp = await client.delete("/api/v1/documents/missing", headers=auth_headers())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_removes_file(client, mock_db):
    mock_db.documents.find_one = AsyncMock(return_value=mock_doc())
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_rm:
        resp = await client.delete("/api/v1/documents/doc-1", headers=auth_headers())
    assert resp.status_code == 204
    mock_rm.assert_called_once()
