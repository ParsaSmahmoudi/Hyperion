"""Tests for core modules (no LLM required)"""
import re
import pytest


def test_decompose_parser():
    from hyperion.core.decomposer import ProblemDecomposer

    class FakeLLM:
        async def chat(self, messages, **kwargs):
            return "Sub-problem 1: First thing to analyze\nSub-problem 2: Second thing to do\nSub-problem 3: Third thing to handle properly"

    d = ProblemDecomposer(llm=FakeLLM())

    import asyncio
    result = asyncio.run(d.decompose("Test problem"))
    assert len(result) == 3
    assert "First thing" in result[0]
    assert "Third thing" in result[2]


def test_explorer_parser():
    from hyperion.core.explorer import MultiPathExplorer

    class FakeLLM:
        async def chat(self, messages, **kwargs):
            return """Approach 1: First approach
Some details about it.

Approach 2: Second approach
More details."""

    e = MultiPathExplorer(llm=FakeLLM())

    import asyncio
    result = asyncio.run(e.explore("sub-problem", "main problem"))
    assert len(result) >= 1
    assert "approach" in result[0].lower() or "Approach" in result[0]


def test_synthesizer_format():
    from hyperion.core.synthesizer import Synthesizer

    class FakeLLM:
        async def chat(self, messages, **kwargs):
            return "Combined answer with all insights."

    s = Synthesizer(llm=FakeLLM())
    import asyncio
    result = asyncio.run(s.synthesize("main problem", ["solution 1", "solution 2"]))
    assert "Combined" in result


def test_verifier_extract():
    from hyperion.core.verifier import Verifier

    class FakeLLM:
        async def chat(self, messages, **kwargs):
            return """VERIFIED
This is the final answer.
It is well structured."""

    v = Verifier(llm=FakeLLM())
    import asyncio
    result = asyncio.run(v.verify("problem", "draft"))
    assert "final answer" in result.lower()


def test_verifier_corrected():
    from hyperion.core.verifier import Verifier

    class FakeLLM:
        async def chat(self, messages, **kwargs):
            return """FAILED: missing detail
CORRECTED:
The corrected final answer with all details."""

    v = Verifier(llm=FakeLLM())
    import asyncio
    result = asyncio.run(v.verify("problem", "draft"))
    assert "corrected" in result.lower()
