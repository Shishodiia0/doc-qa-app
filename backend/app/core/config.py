from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Doc QA App"
    groq_api_key: str
    openai_api_key: str = ""
    mongodb_url: str = "mongodb://mongo:27017"
    mongodb_db: str = "docqa"
    redis_url: str = "redis://redis:6379"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    max_file_size_mb: int = 100
    upload_dir: str = "/tmp/uploads"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
