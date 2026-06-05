"""
Example 5: Using local Ollama (no API key needed)
Run: python examples/05_ollama.py
Requires Ollama installed: https://ollama.ai
And model pulled: ollama pull llama3.1
"""
import asyncio
import os

from hyperion.core.hyperion import HyperionEngine
from hyperion.models.router import ModelRouter


async def main():
    router = ModelRouter(
        backend="ollama",
        base_url="http://localhost:11434",
        fast_model="llama3.1:8b",
        strong_model="llama3.1:70b"  # if you have it
    )

    engine = HyperionEngine(router=router, verbose=True)
    answer = await engine.solve("Explain the difference between TCP and UDP.")
    print(f"\n=== ANSWER ===\n{answer}")
    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
