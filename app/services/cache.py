import redis.asyncio as redis
from typing import Optional, Any
import json
from app.core.config import settings


class CacheService:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        self._client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            data = await self._client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self._client:
            return False
        try:
            await self._client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        if not self._client:
            return False
        try:
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
            return True
        except Exception:
            return False


cache_service = CacheService()