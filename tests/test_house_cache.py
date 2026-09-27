"""Unit tests for house cache failure isolation and invalidation."""

from unittest.mock import MagicMock, call

from app.services import house_cache


def test_set_cache_does_not_pollute_local_cache_when_redis_fails(monkeypatch):
    redis_client = MagicMock()
    redis_client.setex.side_effect = OSError("offline")
    local_cache = {}
    monkeypatch.setattr(house_cache, "_get_redis", lambda: redis_client)
    monkeypatch.setattr(house_cache, "_get_local_cache", lambda: local_cache)

    house_cache.RedisCache.set_cache("house:1", {"id": 1})

    assert local_cache == {}


def test_delete_cache_still_clears_local_when_redis_fails(monkeypatch):
    redis_client = MagicMock()
    redis_client.delete.side_effect = OSError("offline")
    local_cache = {"house:1": {"id": 1}}
    monkeypatch.setattr(house_cache, "_get_redis", lambda: redis_client)
    monkeypatch.setattr(house_cache, "_get_local_cache", lambda: local_cache)

    house_cache.RedisCache.delete_cache("house:1")

    assert local_cache == {}


def test_invalidate_house_caches_clears_all_dependent_keys(monkeypatch):
    delete_cache = MagicMock()
    delete_by_prefix = MagicMock()
    monkeypatch.setattr(house_cache.RedisCache, "delete_cache", delete_cache)
    monkeypatch.setattr(house_cache.RedisCache, "delete_by_prefix", delete_by_prefix)

    house_cache.invalidate_house_caches(42)

    assert delete_cache.call_args_list == [
        call("house_info:42"),
        call("house_hot_lists"),
        call("house_hot_lists:v2"),
        call("house_new_lists"),
        call("house_new_lists:v2"),
    ]
    delete_by_prefix.assert_called_once_with("all_house_infos_count")
