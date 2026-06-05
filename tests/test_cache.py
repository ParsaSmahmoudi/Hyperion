"""Tests for Hyperion cache"""
import os
import time
import pytest
from hyperion.models.async_backend import get_cache, _cache_key, AsyncLLM


def test_cache_key_deterministic():
    msgs = [{"role": "user", "content": "hello"}]
    k1 = _cache_key(msgs, "model", 0.7, 1000)
    k2 = _cache_key(msgs, "model", 0.7, 1000)
    assert k1 == k2
    assert len(k1) == 64


def test_cache_key_changes_with_params():
    msgs = [{"role": "user", "content": "hello"}]
    k1 = _cache_key(msgs, "model", 0.7, 1000)
    k2 = _cache_key(msgs, "model", 0.9, 1000)
    assert k1 != k2


def test_cache_set_get():
    cache = get_cache()
    cache.set("test_key_xyz", "test_value", expire=60)
    assert cache.get("test_key_xyz") == "test_value"
    cache.delete("test_key_xyz")


def test_cache_ttl():
    cache = get_cache()
    cache.set("ttl_test", "value", expire=1)
    assert cache.get("ttl_test") == "value"
    time.sleep(1.2)
    assert cache.get("ttl_test") is None
