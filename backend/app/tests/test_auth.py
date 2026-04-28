import pytest
from unittest.mock import AsyncMock, patch
from app.core.security import hash_password


# ── register ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)
    resp = await client.post("/api/v1/auth/register", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value={"_id": "u1", "username": "alice"})
    resp = await client.post("/api/v1/auth/register", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 400
    assert "already taken" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_missing_fields(client):
    resp = await client.post("/api/v1/auth/register", json={"username": "alice"})
    assert resp.status_code == 422


# ── login ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value={
        "_id": "u1", "username": "alice", "password": hash_password("secret")
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value={
        "_id": "u1", "username": "alice", "password": hash_password("secret")
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client, mock_db):
    mock_db.users.find_one = AsyncMock(return_value=None)
    resp = await client.post("/api/v1/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_no_token(client):
    resp = await client.get("/api/v1/documents/")
    assert resp.status_code in (401, 403)
