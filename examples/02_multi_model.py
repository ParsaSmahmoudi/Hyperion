"""
Example 2: Multi-model routing
Use a fast model for exploration and a strong model for synthesis.
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.models.router import ModelRouter


async def main():
    router = ModelRouter(
        fast_model="openai/gpt-4o-mini",
        strong_model="openai/gpt-4o"
    )

    engine = HyperionEngine(router=router, verbose=True)
    answer = await engine.solve(
        "Explain quantum entanglement in a way a high schooler can understand."
    )
    print(f"\n=== ANSWER ===\n{answer}")
    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
