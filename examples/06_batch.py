"""
Example 6: Batch processing
Solve many questions in parallel.
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.models.router import ModelRouter


QUESTIONS = [
    "What is Python's GIL?",
    "How does git rebase differ from merge?",
    "What causes a stack overflow?",
    "Why is Big-O important?",
    "What is the CAP theorem?",
]


async def solve_one(engine, q):
    return await engine.solve(q)


async def main():
    router = ModelRouter()
    engine = HyperionEngine(router=router, verbose=False)

    print(f"Solving {len(QUESTIONS)} questions in parallel...\n")
    answers = await asyncio.gather(*[solve_one(engine, q) for q in QUESTIONS])

    for q, a in zip(QUESTIONS, answers):
        print(f"\nQ: {q}")
        print(f"A: {a[:200]}...")

    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
