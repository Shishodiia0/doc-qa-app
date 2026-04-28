import json
import numpy as np
from typing import Optional
from app.core.database import get_redis, get_redis_bytes


async def cache_get(key: str) -> Optional[str]:
    redis = await get_redis()
    return await redis.get(key)


async def cache_set(key: str, value: str, ttl: int = 3600):
    redis = await get_redis()
    await redis.setex(key, ttl, value)


async def cache_delete(key: str):
    redis = await get_redis()
    await redis.delete(key)


async def store_index_data(doc_id: str, chunks: list, vectors_bytes: bytes):
    text_redis = await get_redis()
    bin_redis = await get_redis_bytes()
    await text_redis.setex(f"chunks:{doc_id}", 86400, json.dumps(chunks))
    await bin_redis.setex(f"vectors:{doc_id}", 86400, vectors_bytes)


async def load_index_data(doc_id: str):
    text_redis = await get_redis()
    bin_redis = await get_redis_bytes()
    chunks_raw = await text_redis.get(f"chunks:{doc_id}")
    vectors_raw = await bin_redis.get(f"vectors:{doc_id}")
    if not chunks_raw or not vectors_raw:
        return None, None
    chunks = json.loads(chunks_raw)
    vectors = np.frombuffer(vectors_raw, dtype=np.float32).reshape(-1, 256)
    return chunks, vectors
