# exts/redis.py
from flask_redis import FlaskRedis
from datetime import timedelta
import json
import logging
from cachetools import TTLCache

logger = logging.getLogger(__name__)

redis_store = FlaskRedis()

# 配置默认缓存过期时间,5分钟
DEFAULT_CACHE_TIMEOUT = timedelta(minutes=5)

# L1 本地内存缓存：30 秒 TTL，最多 256 条，线程安全
LOCAL_CACHE_TTL = 30
LOCAL_CACHE_MAXSIZE = 256
local_cache = TTLCache(maxsize=LOCAL_CACHE_MAXSIZE, ttl=LOCAL_CACHE_TTL)


def is_redis_available():
    """检查 Redis 是否可用"""
    try:
        redis_store.ping()
        return True
    except Exception:
        return False


class RedisCache:
    @staticmethod
    def get_cache(key):
        """获取缓存数据，L1 本地 → L2 Redis，不可用时返回 None"""
        # L1: 本地内存
        try:
            if key in local_cache:
                return local_cache[key]
        except Exception:
            pass

        # L2: Redis
        try:
            cached_data = redis_store.get(key)
            if cached_data:
                data = json.loads(cached_data)
                # 回填 L1
                try:
                    local_cache[key] = data
                except Exception:
                    pass
                return data
        except Exception as e:
            logger.warning(f"Redis get_cache('{key}') 失败: {e}")
        return None

    @staticmethod
    def set_cache(key, data, timeout=DEFAULT_CACHE_TIMEOUT):
        """设置缓存数据，先写 L2 再写 L1，保证 L2 失败时 L1 不被污染"""
        # L2 先写，失败时 L1 不更新，下次读走 DB，保证一致性
        try:
            redis_store.setex(key, timeout, json.dumps(data))
        except Exception as e:
            logger.warning(f"Redis set_cache('{key}') 失败: {e}")
            return
        # L2 成功后才写 L1
        try:
            local_cache[key] = data
        except Exception:
            pass

    @staticmethod
    def delete_cache(key):
        """删除缓存数据，先删 L2 再删 L1，防止 L2 删除失败时旧数据从 L2 回灌 L1"""
        # L2 先删，失败时 L1 保留旧数据（最多 30s），好过 L2 旧数据回灌
        try:
            redis_store.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete_cache('{key}') 失败: {e}")
        # L2 删除后再清 L1
        try:
            local_cache.pop(key, None)
        except Exception:
            pass

    @staticmethod
    def exists(key):
        """检查缓存是否存在，先查 L1 再查 Redis"""
        try:
            if key in local_cache:
                return True
        except Exception:
            pass
        try:
            return redis_store.exists(key)
        except Exception:
            return False

    @staticmethod
    def delete_by_prefix(prefix):
        """删除所有匹配前缀的缓存键，先删 L2 再删 L1"""
        # L2: Redis SCAN 先删，防止 L2 删除失败时旧数据回灌 L1
        try:
            cursor = 0
            while True:
                cursor, keys = redis_store.scan(cursor, match=f'{prefix}*', count=100)
                if keys:
                    redis_store.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Redis delete_by_prefix('{prefix}') 失败: {e}")
        # L2 删除后清 L1
        try:
            keys_to_del = [k for k in local_cache if k.startswith(prefix)]
            for k in keys_to_del:
                local_cache.pop(k, None)
        except Exception:
            pass
