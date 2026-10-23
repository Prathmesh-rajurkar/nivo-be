"""Cache service - disabled (no Redis)."""
from typing import Optional, Any


class CacheService:
    """No-op cache service when Redis is not available."""

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def get(self, key: str) -> Optional[Any]:
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        return True

    async def delete(self, key: str) -> bool:
        return True

    async def delete_pattern(self, pattern: str) -> bool:
        return True


cache_service = CacheService()