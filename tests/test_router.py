"""Tests for model routing"""
import os
import pytest


def test_router_initialization():
    from hyperion.models.router import ModelRouter, FAST_MODELS, STRONG_MODELS
    r = ModelRouter(api_key="test", backend="openrouter")
    assert r.fast_model in FAST_MODELS.get("openrouter", [])
    assert r.strong_model in STRONG_MODELS.get("openrouter", [])


def test_router_lazy_load():
    from hyperion.models.router import ModelRouter
    r = ModelRouter(api_key="test", backend="openrouter", fast_model="test-fast", strong_model="test-strong")
    fast = r.fast()
    fast2 = r.fast()
    assert fast is fast2  # Cached
    strong = r.strong()
    assert fast is not strong


def test_router_override():
    from hyperion.models.router import ModelRouter
    r = ModelRouter(api_key="test", backend="openrouter", fast_model="custom-fast")
    assert r.fast_model == "custom-fast"
