"""
Example 1: Basic usage
Run: python examples/01_basic.py
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.models.router import ModelRouter


async def main():
    router = ModelRouter()
    engine = HyperionEngine(router=router, verbose=True)

    question = "What are 3 effective ways to debug Python code?"
    print(f"\nQuestion: {question}\n")

    answer = await engine.solve(question)
    print(f"\n=== ANSWER ===\n{answer}")

    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
