from typing import List, AsyncGenerator
from groq import AsyncGroq
from app.core.config import get_settings
from app.models.schemas import ChatMessage

settings = get_settings()
client = AsyncGroq(api_key=settings.groq_api_key)
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on provided document context. "
    "Answer only from the context. If the answer is not in the context, say so clearly. "
    "Be concise and accurate."
)


def build_messages(context: str, question: str, history: List[ChatMessage]) -> List[dict]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Document context:\n{context}"},
    ]
    for msg in history[-6:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": question})
    return messages


async def chat_completion(context: str, question: str, history: List[ChatMessage]) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=build_messages(context, question, history),
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content


async def chat_completion_stream(
    context: str, question: str, history: List[ChatMessage]
) -> AsyncGenerator[str, None]:
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=build_messages(context, question, history),
        max_tokens=1024,
        temperature=0.2,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
