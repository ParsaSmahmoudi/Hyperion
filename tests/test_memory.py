"""Tests for memory system"""
import os
import tempfile
import pytest
from hyperion.core.memory import MemoryStore


@pytest.fixture
def temp_memory():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield MemoryStore(memory_dir=tmpdir)


def test_store_and_recall(temp_memory):
    key = temp_memory.store(
        "How do I learn Python?",
        "Practice daily, build projects, read docs, join community.",
        sub_problems=["Setup environment", "Learn basics", "Build projects"],
        tags=["python", "learning", "programming"]
    )
    assert key is not None
    memories = temp_memory.recall("Python programming basics")
    assert len(memories) > 0
    assert "python" in memories[0]["problem"].lower() or "python" in str(memories[0].get("tags", [])).lower()


def test_get_context_for(temp_memory):
    temp_memory.store(
        "What is recursion?",
        "Recursion is when a function calls itself.",
        tags=["recursion", "programming"]
    )
    ctx = temp_memory.get_context_for("recursion in programming")
    assert "PREVIOUS" in ctx
    assert "recursion" in ctx.lower()


def test_memory_clear(temp_memory):
    temp_memory.store("Q1", "A1")
    temp_memory.store("Q2", "A2")
    temp_memory.clear()
    assert temp_memory.recall("Q1") == []


def test_empty_memory(temp_memory):
    assert temp_memory.recall("anything") == []
    assert temp_memory.get_context_for("anything") == ""


def test_duplicate_store(temp_memory):
    temp_memory.store("Test Q", "Test A")
    temp_memory.store("Test Q", "Test A 2")
    memories = temp_memory.recall("Test Q")
    assert len(memories) >= 1
