import os
from ..models.async_backend import AsyncLLM


class KnowledgeExpander:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def expand(self, problem: str, llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        prompt = f"""Given this problem: "{problem}"

Generate 3-5 key pieces of CONTEXT or BACKGROUND KNOWLEDGE that would help solve this problem more effectively. Consider:
- Relevant concepts, frameworks, or theories
- Common misconceptions or pitfalls
- Related domains that offer useful insights
- Key criteria for evaluating solutions

Format each as a brief insight. Be concise."""
        messages = [
            {"role": "system", "content": "You expand problem context with relevant knowledge."},
            {"role": "user", "content": prompt}
        ]
        return await llm.chat(messages, use_cache=use_cache)
