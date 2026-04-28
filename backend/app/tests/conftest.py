import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token


# ── helpers ──────────────────────────────────────────────────────────────────

def make_token(user_id: str = "user-123") -> str:
    return create_access_token({"sub": user_id})


def auth_headers(user_id: str = "user-123") -> dict:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


def mock_doc(overrides: dict = {}) -> dict:
    base = {
        "_id": "doc-1",
        "filename": "test.pdf",
        "file_type": "pdf",
        "user_id": "user-123",
        "status": "ready",
        "summary": "A test summary.",
        "transcript_segments": None,
        "file_path": "/tmp/test.pdf",
        "created_at": datetime.utcnow(),
        "text": "This is test document content about machine learning.",
        "chunks": ["This is test document content about machine learning."],
    }
    base.update(overrides)
    return base


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.users.find_one = AsyncMock(return_value=None)
    db.users.insert_one = AsyncMock()
    db.documents.find_one = AsyncMock(return_value=None)
    db.documents.insert_one = AsyncMock()
    db.documents.update_one = AsyncMock()
    db.documents.delete_one = AsyncMock()
    db.documents.find = MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[])))
    return db


@pytest_asyncio.fixture
async def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
