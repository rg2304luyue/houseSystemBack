# exts/redis.py
from flask_redis import FlaskRedis
from datetime import timedelta
import json

redis_store = FlaskRedis()

# 配置默认缓存过期时间,5分钟
DEFAULT_CACHE_TIMEOUT = timedelta(minutes=5)

class RedisCache:
    @staticmethod
    def get_cache(key):
        """获取缓存数据"""
        cached_data = redis_store.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    @staticmethod
    def set_cache(key, data, timeout=DEFAULT_CACHE_TIMEOUT):
        """设置缓存数据"""
        redis_store.setex(key, timeout, json.dumps(data))

    @staticmethod
    def delete_cache(key):
        """删除缓存数据"""
        redis_store.delete(key)

    @staticmethod
    def exists(key):
        """检查缓存是否存在"""
        return redis_store.exists(key)

    @staticmethod
    def delete_by_prefix(prefix):
        """删除所有匹配前缀的缓存键（使用 SCAN，非阻塞）"""
        cursor = 0
        while True:
            cursor, keys = redis_store.scan(cursor, match=f'{prefix}*', count=100)
            if keys:
                redis_store.delete(*keys)
            if cursor == 0:
                break