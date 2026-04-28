import motor.motor_asyncio
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()

_mongo_client: motor.motor_asyncio.AsyncIOMotorClient = None
_redis_text: aioredis.Redis = None   # for text/json (decode_responses=True)
_redis_bytes: aioredis.Redis = None  # for binary vectors (decode_responses=False)


def get_mongo_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
    return _mongo_client


def get_db():
    return get_mongo_client()[settings.mongodb_db]


async def get_redis() -> aioredis.Redis:
    global _redis_text
    if _redis_text is None:
        _redis_text = await aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_text


async def get_redis_bytes() -> aioredis.Redis:
    global _redis_bytes
    if _redis_bytes is None:
        _redis_bytes = await aioredis.from_url(settings.redis_url, decode_responses=False)
    return _redis_bytes


async def close_connections():
    global _mongo_client, _redis_text, _redis_bytes
    if _mongo_client:
        _mongo_client.close()
    if _redis_text:
        await _redis_text.close()
    if _redis_bytes:
        await _redis_bytes.close()
