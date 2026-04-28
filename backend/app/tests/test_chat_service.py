import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.chat_service import build_messages, chat_completion, chat_completion_stream
from app.models.schemas import ChatMessage


def test_build_messages_basic():
    msgs = build_messages("some context", "What is AI?", [])
    roles = [m["role"] for m in msgs]
    assert "system" in roles
    assert msgs[-1]["role"] == "user"
    assert msgs[-1]["content"] == "What is AI?"


def test_build_messages_with_history():
    history = [
        ChatMessage(role="user", content="Hello"),
        ChatMessage(role="assistant", content="Hi there"),
    ]
    msgs = build_messages("ctx", "Follow up?", history)
    contents = [m["content"] for m in msgs]
    assert "Hello" in contents
    assert "Hi there" in contents
    assert "Follow up?" in contents


def test_build_messages_history_truncated():
    history = [ChatMessage(role="user", content=f"msg{i}") for i in range(20)]
    msgs = build_messages("ctx", "final", history)
    user_msgs = [m for m in msgs if m["role"] == "user"]
    assert len(user_msgs) <= 7


def test_build_messages_context_included():
    msgs = build_messages("important context here", "question", [])
    system_contents = " ".join(m["content"] for m in msgs if m["role"] == "system")
    assert "important context here" in system_contents


@pytest.mark.asyncio
async def test_chat_completion():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "The answer is 42."
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    with patch("app.services.chat_service.client", mock_client):
        result = await chat_completion("context", "What is the answer?", [])
    assert result == "The answer is 42."


@pytest.mark.asyncio
async def test_chat_completion_stream():
    async def fake_stream():
        for content in ["Hello", " world"]:
            chunk = MagicMock()
            chunk.choices[0].delta.content = content
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_stream())
    with patch("app.services.chat_service.client", mock_client):
        tokens = []
        async for token in chat_completion_stream("ctx", "hi", []):
            tokens.append(token)
    assert "".join(tokens) == "Hello world"


@pytest.mark.asyncio
async def test_chat_completion_stream_skips_none():
    async def fake_stream():
        for content in ["token1", None, "token2"]:
            chunk = MagicMock()
            chunk.choices[0].delta.content = content
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=fake_stream())
    with patch("app.services.chat_service.client", mock_client):
        tokens = []
        async for token in chat_completion_stream("ctx", "hi", []):
            tokens.append(token)
    assert tokens == ["token1", "token2"]
