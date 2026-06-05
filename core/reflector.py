import re
from ..models.async_backend import AsyncLLM


class MetaReflector:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def reflect(self, problem: str, answer: str, intermediate_solutions: list = None,
                      llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        prompt = f"""ORIGINAL PROBLEM: {problem}
DRAFT ANSWER: {answer}

Now do a META-REFLECTION on this answer:

1. SELF-CRITIQUE: What are the 3 weakest points of this answer?
2. IMPROVEMENT: How would you strengthen each weak point?
3. BLIND SPOTS: What perspectives or angles might have been missed?
4. FINAL POLISH: Provide the FINAL, IMPROVED version of the answer.

The final answer must be complete, well-structured, and directly address the original problem.
Mark the final version with "FINAL ANSWER:" at the start.
"""
        messages = [
            {"role": "system", "content": "You are a meta-cognitive reflector. You analyze answers at a higher level and refine them to perfection."},
            {"role": "user", "content": prompt}
        ]
        result = await llm.chat(messages, use_cache=use_cache)
        m = re.search(r'(?:FINAL ANSWER|Final Answer|Final answer)[:\s]*\n*(.*?)$', result, re.DOTALL)
        if m:
            return m.group(1).strip()
        return result
