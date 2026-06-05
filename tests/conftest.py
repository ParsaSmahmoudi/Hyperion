"""Pytest config and fixtures"""
import os
import sys
import pytest

# Add parent to path so we can import hyperion
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def disable_ssl_verify(monkeypatch):
    monkeypatch.setenv("HYPERION_SSL_VERIFY", "false")


@pytest.fixture
def mock_api_key(monkeypatch):
    monkeypatch.setenv("HYPERION_API_KEY", "test-key-no-real-calls")
