import pytest
from app.core.security import (
    hash_password, verify_password, create_access_token, decode_token
)
from fastapi import HTTPException


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_different_each_time():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2


def test_create_and_decode_token():
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_decode_invalid_token():
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token")
    assert exc.value.status_code == 401


def test_decode_tampered_token():
    token = create_access_token({"sub": "user-1"})
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException):
        decode_token(tampered)


def test_token_contains_expiry():
    token = create_access_token({"sub": "user-1"})
    payload = decode_token(token)
    assert "exp" in payload
