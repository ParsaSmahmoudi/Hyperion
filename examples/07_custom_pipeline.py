"""
Example 7: Programmatic API (use Hyperion as a library)
Build your own applications on top of Hyperion's reasoning engine.
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.core.decomposer import ProblemDecomposer
from hyperion.core.explorer import MultiPathExplorer
from hyperion.core.reasoner import DeepReasoner
from hyperion.core.critic import SelfCritic
from hyperion.models.router import ModelRouter


async def custom_pipeline(question: str) -> dict:
    """Build a custom reasoning pipeline"""
    fast_llm = ModelRouter().fast()
    strong_llm = ModelRouter().strong()

    decomposer = ProblemDecomposer(fast_llm)
    explorer = MultiPathExplorer(fast_llm)
    reasoner = DeepReasoner(fast_llm)
    critic = SelfCritic(strong_llm)

    sub_problems = await decomposer.decompose(question, fast_llm)

    results = []
    for sp in sub_problems:
        paths = await explorer.explore(sp, question, fast_llm)
        reasoning = await reasoner.reason(sp, paths[0], fast_llm)
        refined = await critic.critique(sp, reasoning, strong_llm)
        results.append({"sub_problem": sp, "solution": refined})

    return {"question": question, "results": results}


async def main():
    result = await custom_pipeline("Design a scalable URL shortener")
    print(f"\nQuestion: {result['question']}")
    for r in result["results"]:
        print(f"\nSub-problem: {r['sub_problem']}")
        print(f"Solution: {r['solution'][:300]}...")


if __name__ == "__main__":
    asyncio.run(main())
