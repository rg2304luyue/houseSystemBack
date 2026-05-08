# exts/redis.py
from flask_redis import FlaskRedis
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

redis_store = FlaskRedis()

# 配置默认缓存过期时间,5分钟
DEFAULT_CACHE_TIMEOUT = timedelta(minutes=5)


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
        """获取缓存数据，Redis 不可用时返回 None"""
        try:
            cached_data = redis_store.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis get_cache('{key}') 失败: {e}")
        return None

    @staticmethod
    def set_cache(key, data, timeout=DEFAULT_CACHE_TIMEOUT):
        """设置缓存数据，Redis 不可用时静默跳过"""
        try:
            redis_store.setex(key, timeout, json.dumps(data))
        except Exception as e:
            logger.warning(f"Redis set_cache('{key}') 失败: {e}")

    @staticmethod
    def delete_cache(key):
        """删除缓存数据，Redis 不可用时静默跳过"""
        try:
            redis_store.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete_cache('{key}') 失败: {e}")

    @staticmethod
    def exists(key):
        """检查缓存是否存在，Redis 不可用时返回 False"""
        try:
            return redis_store.exists(key)
        except Exception:
            return False

    @staticmethod
    def delete_by_prefix(prefix):
        """删除所有匹配前缀的缓存键（使用 SCAN，非阻塞），Redis 不可用时静默跳过"""
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
