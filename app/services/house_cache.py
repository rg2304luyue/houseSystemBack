"""Two-level caching and invalidation for house read models."""

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_TIMEOUT = 300
_LOCAL_CACHE_TTL = 30
_LOCAL_CACHE_MAXSIZE = 256
_redis_client = None
_local_cache = None


def _get_redis():
    """Return the lazily initialized Redis client."""
    global _redis_client
    if _redis_client is None:
        import redis as redis_module
        _redis_client = redis_module.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def _get_local_cache():
    """Return the process-local TTL cache."""
    global _local_cache
    if _local_cache is None:
        from cachetools import TTLCache
        _local_cache = TTLCache(maxsize=_LOCAL_CACHE_MAXSIZE, ttl=_LOCAL_CACHE_TTL)
    return _local_cache


class RedisCache:
    """Best-effort L1 local and L2 Redis cache facade."""

    @staticmethod
    def get_cache(key: str):
        """Read L1 then L2, returning ``None`` on errors or misses."""
        local = _get_local_cache()
        try:
            if key in local:
                return local[key]
        except Exception:
            pass
        try:
            raw = _get_redis().get(key)
            if raw:
                data = json.loads(raw)
                try:
                    local[key] = data
                except Exception:
                    pass
                return data
        except Exception as error:
            logger.warning("Redis get_cache('%s') failed: %s", key, error)
        return None

    @staticmethod
    def set_cache(key: str, data, timeout: int = _DEFAULT_CACHE_TIMEOUT):
        """Write L2 before L1 so an L2 failure cannot pollute L1."""
        try:
            _get_redis().setex(key, timeout, json.dumps(data))
        except Exception as error:
            logger.warning("Redis set_cache('%s') failed: %s", key, error)
            return
        try:
            _get_local_cache()[key] = data
        except Exception:
            pass

    @staticmethod
    def delete_cache(key: str):
        """Delete a key independently from both cache levels."""
        try:
            _get_redis().delete(key)
        except Exception as error:
            logger.warning("Redis delete_cache('%s') failed: %s", key, error)
        try:
            _get_local_cache().pop(key, None)
        except Exception:
            pass

    @staticmethod
    def delete_by_prefix(prefix: str):
        """Scan-delete matching L2 keys and purge matching L1 keys."""
        try:
            redis_client = _get_redis()
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor, match=f"{prefix}*", count=100)
                if keys:
                    redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as error:
            logger.warning("Redis delete_by_prefix('%s') failed: %s", prefix, error)
        try:
            local = _get_local_cache()
            for key in [key for key in local if key.startswith(prefix)]:
                local.pop(key, None)
        except Exception:
            pass


def invalidate_house_caches(house_id: int | None = None) -> None:
    """Invalidate every house view affected by an availability change."""
    if house_id is not None:
        RedisCache.delete_cache(f"house_info:{house_id}")
    # Prefix-delete so versioned keys (":v2", ":v3", ...) can never drift out
    # of sync with the read side again.
    RedisCache.delete_by_prefix("house_hot_lists")
    RedisCache.delete_by_prefix("house_new_lists")
    RedisCache.delete_by_prefix("all_house_infos_count")
