from typing import Optional
from redis.asyncio import Redis
from src.core.config import settings

redis: Optional[Redis] = None


# Функция понадобится при внедрении зависимостей
async def get_redis() -> Optional[Redis]:
    redis = Redis(host=settings.redis_host, port=settings.redis_port)
    return redis
