"""
Example 3: With memory and tools
This shows how Hyperion can recall past solutions and use tools (calculator, web, code).
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.core.memory import MemoryStore
from hyperion.core.tools import ToolRegistry
from hyperion.models.router import ModelRouter


async def main():
    router = ModelRouter()
    memory = MemoryStore()
    tools = ToolRegistry()

    engine = HyperionEngine(
        router=router, memory=memory, tools=tools, verbose=True
    )

    print("First question...")
    await engine.solve("What is the capital of France?")

    print("\n\nSecond question (should recall previous)...")
    answer = await engine.solve("And what language do they speak there?")
    print(f"\n=== ANSWER ===\n{answer}")

    print("\n\nThird question (with calculation)...")
    answer = await engine.solve(
        "If a car travels at 60 mph for 2.5 hours, how far does it go? Use calculator."
    )
    print(f"\n=== ANSWER ===\n{answer}")

    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
