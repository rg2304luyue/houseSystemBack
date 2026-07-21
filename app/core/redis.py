"""Redis client for FastAPI — simple wrapper around redis-py."""
import redis as redis_lib
from app.core.config import settings

_redis_client: redis_lib.Redis | None = None


def get_redis() -> redis_lib.Redis:
    """Lazy-init and return a Redis client from settings.REDIS_URL."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_lib.Redis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
    return _redis_client


def is_redis_available() -> bool:
    """Check whether Redis is reachable."""
    try:
        get_redis().ping()
        return True
    except Exception:
        return False
